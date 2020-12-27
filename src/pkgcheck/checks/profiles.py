"""Various profile-related checks."""

import os
from collections import defaultdict

from pkgcore.ebuild import misc
from pkgcore.ebuild import profiles as profiles_mod
from pkgcore.ebuild.atom import atom as atom_cls
from pkgcore.ebuild.repo_objs import Profiles
from snakeoil.mappings import ImmutableDict
from snakeoil.osutils import pjoin
from snakeoil.sequences import iflatten_instance
from snakeoil.strings import pluralism

from .. import addons, base, results, sources
from ..profiles import ProfileAddon, ProfileNode
from . import Check


class UnknownProfilePackage(results.ProfilesResult, results.Warning):
    """Profile files includes package entry that doesn't exist in the repo."""

    def __init__(self, path, atom):
        super().__init__()
        self.path = path
        self.atom = str(atom)

    @property
    def desc(self):
        return f'{self.path!r}: unknown package: {self.atom!r}'


class UnknownProfilePackageUse(results.ProfilesResult, results.Warning):
    """Profile files include entries with USE flags that aren't used on any matching packages."""

    def __init__(self, path, atom, flags):
        super().__init__()
        self.path = path
        self.atom = str(atom)
        self.flags = tuple(flags)

    @property
    def desc(self):
        s = pluralism(self.flags)
        flags = ', '.join(self.flags)
        atom = f'{self.atom}[{flags}]'
        return f'{self.path!r}: unknown package USE flag{s}: {atom!r}'


class UnknownProfileUse(results.ProfilesResult, results.Warning):
    """Profile files include USE flags that don't exist."""

    def __init__(self, path, flags):
        super().__init__()
        self.path = path
        self.flags = tuple(flags)

    @property
    def desc(self):
        s = pluralism(self.flags)
        flags = ', '.join(map(repr, self.flags))
        return f'{self.path!r}: unknown USE flag{s}: {flags}'


class UnknownProfilePackageKeywords(results.ProfilesResult, results.Warning):
    """Profile files include package keywords that don't exist."""

    def __init__(self, path, atom, keywords):
        super().__init__()
        self.path = path
        self.atom = str(atom)
        self.keywords = tuple(keywords)

    @property
    def desc(self):
        s = pluralism(self.keywords)
        keywords = ', '.join(map(repr, self.keywords))
        return f'{self.path!r}: unknown package keyword{s}: {self.atom}: {keywords}'


class ProfileWarning(results.ProfilesResult, results.LogWarning):
    """Badly formatted data in various profile files."""


class ProfileError(results.ProfilesResult, results.LogError):
    """Erroneously formatted data in various profile files."""


# mapping of profile log levels to result classes
_logs_to_results = ImmutableDict({
    'pkgcore.log.logger.warning': ProfileWarning,
    'pkgcore.log.logger.error': ProfileError,
})


def verify_files(*files):
    """Decorator to register file verification methods."""

    class decorator:
        """Decorator with access to the class of a decorated function."""

        def __init__(self, func):
            self.func = func

        def __set_name__(self, owner, name):
            for file, attr in files:
                owner.known_files[file] = (attr, self.func)
            setattr(owner, name, self.func)

    return decorator


class ProfilesCheck(Check):
    """Scan repo profiles for unknown flags/packages."""

    _source = sources.ProfilesRepoSource
    required_addons = (addons.UseAddon, addons.KeywordsAddon)
    known_results = frozenset([
        UnknownProfilePackage, UnknownProfilePackageUse, UnknownProfileUse,
        UnknownProfilePackageKeywords, ProfileWarning, ProfileError,
    ])

    # mapping between known files and verification methods
    known_files = {}

    def __init__(self, *args, use_addon, keywords_addon):
        super().__init__(*args)
        target_repo = self.options.target_repo
        self.keywords = keywords_addon
        self.search_repo = self.options.search_repo
        self.profiles_dir = target_repo.config.profiles_base

        local_iuse = {use for pkg, (use, desc) in target_repo.config.use_local_desc}
        self.available_iuse = frozenset(
            local_iuse | use_addon.global_iuse |
            use_addon.global_iuse_expand | use_addon.global_iuse_implicit)

    @verify_files(('parent', 'parents'),
                  ('eapi', 'eapi'))
    def _pull_attr(self, *args):
        """Verification only needs to pull the profile attr."""
        yield from ()

    @verify_files(('deprecated', 'deprecated'))
    def _deprecated(self, filename, node, vals):
        # make sure replacement profile exists
        if vals is not None:
            replacement, msg = vals
            try:
                ProfileNode(pjoin(self.profiles_dir, replacement))
            except profiles_mod.ProfileError:
                yield ProfileError(
                    f'nonexistent replacement {replacement!r} '
                    f'for deprecated profile: {node.name!r}')

    # non-spec files
    @verify_files(('package.keywords', 'keywords'),
                  ('package.accept_keywords', 'accept_keywords'))
    def _pkg_keywords(self, filename, node, vals):
        for atom, keywords in vals:
            if invalid := sorted(set(keywords) - self.keywords.valid):
                yield UnknownProfilePackageKeywords(
                    pjoin(node.name, filename), atom, invalid)

    @verify_files(('use.force', 'use_force'),
                  ('use.stable.force', 'use_stable_force'),
                  ('use.mask', 'use_mask'),
                  ('use.stable.mask', 'use_stable_mask'))
    def _use(self, filename, node, vals):
        # TODO: give ChunkedDataDict some dict view methods
        d = vals.render_to_dict()
        for _, entries in d.items():
            for _, disabled, enabled in entries:
                if unknown_disabled := set(disabled) - self.available_iuse:
                    flags = ('-' + u for u in unknown_disabled)
                    yield UnknownProfileUse(
                        pjoin(node.name, filename), flags)
                if unknown_enabled := set(enabled) - self.available_iuse:
                    yield UnknownProfileUse(
                        pjoin(node.name, filename), unknown_enabled)

    @verify_files(('packages', 'packages'),
                  ('package.mask', 'masks'),
                  ('package.unmask', 'unmasks'),
                  ('package.deprecated', 'pkg_deprecated'))
    def _pkg_atoms(self, filename, node, vals):
        for x in iflatten_instance(vals, atom_cls):
            if not self.search_repo.match(x):
                yield UnknownProfilePackage(pjoin(node.name, filename), x)

    @verify_files(('package.use', 'pkg_use'),
                  ('package.use.force', 'pkg_use_force'),
                  ('package.use.stable.force', 'pkg_use_stable_force'),
                  ('package.use.mask', 'pkg_use_mask'),
                  ('package.use.stable.mask', 'pkg_use_stable_mask'))
    def _pkg_use(self, filename, node, vals):
        # TODO: give ChunkedDataDict some dict view methods
        d = vals
        if isinstance(d, misc.ChunkedDataDict):
            d = vals.render_to_dict()

        for _pkg, entries in d.items():
            for a, disabled, enabled in entries:
                if pkgs := self.search_repo.match(a):
                    available = {u for pkg in pkgs for u in pkg.iuse_stripped}
                    if unknown_disabled := set(disabled) - available:
                        flags = ('-' + u for u in unknown_disabled)
                        yield UnknownProfilePackageUse(
                            pjoin(node.name, filename), a, flags)
                    if unknown_enabled := set(enabled) - available:
                        yield UnknownProfilePackageUse(
                            pjoin(node.name, filename), a, unknown_enabled)
                else:
                    yield UnknownProfilePackage(
                        pjoin(node.name, filename), a)

    def feed(self, profile):
        for f in profile.files.intersection(self.known_files):
            attr, func = self.known_files[f]
            with base.LogReports(_logs_to_results) as log_reports:
                data = getattr(profile.node, attr)
            yield from func(self, f, profile.node, data)
            yield from log_reports


class UnusedProfileDirs(results.ProfilesResult, results.Warning):
    """Unused profile directories detected."""

    def __init__(self, dirs):
        super().__init__()
        self.dirs = tuple(dirs)

    @property
    def desc(self):
        s = pluralism(self.dirs)
        dirs = ', '.join(map(repr, self.dirs))
        return f'unused profile dir{s}: {dirs}'


class ArchesWithoutProfiles(results.ProfilesResult, results.Warning):
    """Arches without corresponding profile listings."""

    def __init__(self, arches):
        super().__init__()
        self.arches = tuple(arches)

    @property
    def desc(self):
        es = pluralism(self.arches, plural='es')
        arches = ', '.join(self.arches)
        return f'arch{es} without profiles: {arches}'


class NonexistentProfilePath(results.ProfilesResult, results.Error):
    """Specified profile path in profiles.desc doesn't exist."""

    def __init__(self, path):
        super().__init__()
        self.path = path

    @property
    def desc(self):
        return f'nonexistent profile path: {self.path!r}'


class LaggingProfileEapi(results.ProfilesResult, results.Warning):
    """Profile has an EAPI that is older than one of its parents."""

    def __init__(self, profile, eapi, parent, parent_eapi):
        super().__init__()
        self.profile = profile
        self.eapi = eapi
        self.parent = parent
        self.parent_eapi = parent_eapi

    @property
    def desc(self):
        return (
            f'{self.profile!r} profile has EAPI {self.eapi}, '
            f'{self.parent!r} parent has EAPI {self.parent_eapi}'
        )


class UnknownCategoryDirs(results.ProfilesResult, results.Warning):
    """Category directories that aren't listed in a repo's categories.

    Or the categories of the repo's masters as well.
    """

    def __init__(self, dirs):
        super().__init__()
        self.dirs = tuple(dirs)

    @property
    def desc(self):
        dirs = ', '.join(self.dirs)
        s = pluralism(self.dirs)
        return f'unknown category dir{s}: {dirs}'


class NonexistentCategories(results.ProfilesResult, results.Warning):
    """Category entries in profiles/categories that don't exist in the repo."""

    def __init__(self, categories):
        super().__init__()
        self.categories = tuple(categories)

    @property
    def desc(self):
        categories = ', '.join(self.categories)
        ies = pluralism(self.categories, singular='y', plural='ies')
        return f'nonexistent profiles/categories entr{ies}: {categories}'


def dir_parents(path):
    """Yield all directory path parents excluding the root directory.

    Example:
    >>> list(dir_parents('/root/foo/bar/baz'))
    ['root/foo/bar', 'root/foo', 'root']
    """
    path = os.path.normpath(path.strip('/'))
    while path:
        yield path
        dirname, _basename = os.path.split(path)
        path = dirname.rstrip('/')


class RepoProfilesCheck(Check):
    """Scan repo for various profiles directory issues.

    Including unknown arches in profiles, arches without profiles, and unknown
    categories.
    """

    _source = (sources.EmptySource, (base.profiles_scope,))
    required_addons = (ProfileAddon,)
    known_results = frozenset([
        ArchesWithoutProfiles, UnusedProfileDirs, NonexistentProfilePath,
        UnknownCategoryDirs, NonexistentCategories, LaggingProfileEapi,
        ProfileError, ProfileWarning,
    ])

    # known profile status types for the gentoo repo
    known_profile_statuses = frozenset(['stable', 'dev', 'exp'])

    def __init__(self, *args, profile_addon):
        super().__init__(*args)
        self.arches = self.options.target_repo.known_arches
        self.repo = self.options.target_repo
        self.profiles_dir = self.repo.config.profiles_base
        self.non_profile_dirs = profile_addon.non_profile_dirs

    def finish(self):
        if unknown_category_dirs := set(self.repo.category_dirs).difference(self.repo.categories):
            yield UnknownCategoryDirs(sorted(unknown_category_dirs))
        if nonexistent_categories := set(self.repo.config.categories).difference(self.repo.category_dirs):
            yield NonexistentCategories(sorted(nonexistent_categories))

        if arches_without_profiles := set(self.arches) - set(self.repo.profiles.arches()):
            yield ArchesWithoutProfiles(sorted(arches_without_profiles))

        root_profile_dirs = {'embedded'}
        available_profile_dirs = set()
        for root, _dirs, _files in os.walk(self.profiles_dir):
            if d := root[len(self.profiles_dir):].lstrip('/'):
                available_profile_dirs.add(d)
        available_profile_dirs -= self.non_profile_dirs | root_profile_dirs

        # don't check for acceptable profile statuses on overlays
        if self.options.gentoo_repo:
            known_profile_statuses = self.known_profile_statuses
        else:
            known_profile_statuses = None

        # forcibly parse profiles.desc and convert log warnings/errors into reports
        with base.LogReports(_logs_to_results) as log_reports:
            profiles = Profiles.parse(
                self.profiles_dir, self.repo.repo_id,
                known_status=known_profile_statuses, known_arch=self.arches)
        yield from log_reports

        seen_profile_dirs = set()
        lagging_profile_eapi = defaultdict(list)
        for p in profiles:
            try:
                profile = profiles_mod.ProfileStack(pjoin(self.profiles_dir, p.path))
            except profiles_mod.ProfileError:
                yield NonexistentProfilePath(p.path)
                continue
            for parent in profile.stack:
                seen_profile_dirs.update(dir_parents(parent.name))
                # flag lagging profile EAPIs -- assumes EAPIs are sequentially
                # numbered which should be the case for the gentoo repo
                if (self.options.gentoo_repo and str(profile.eapi) < str(parent.eapi)):
                    lagging_profile_eapi[profile].append(parent)

        for profile, parents in lagging_profile_eapi.items():
            parent = parents[-1]
            yield LaggingProfileEapi(
                profile.name, str(profile.eapi), parent.name, str(parent.eapi))

        if unused_profile_dirs := available_profile_dirs - seen_profile_dirs:
            yield UnusedProfileDirs(sorted(unused_profile_dirs))
