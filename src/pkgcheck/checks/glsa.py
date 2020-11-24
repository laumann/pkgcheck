import os

from pkgcore.pkgsets.glsa import GlsaDirSet
from pkgcore.restrictions import packages, values
from pkgcore.restrictions.util import collect_package_restrictions
from snakeoil.cli.arghparse import existent_dir
from snakeoil.osutils import pjoin
from snakeoil.strings import pluralism

from .. import results
from . import GentooRepoCheck, SkipOptionalCheck


class VulnerablePackage(results.VersionResult, results.Error):
    """Packages marked as vulnerable by GLSAs."""

    def __init__(self, arches, glsa, **kwargs):
        super().__init__(**kwargs)
        self.arches = tuple(arches)
        self.glsa = glsa

    @property
    def desc(self):
        s = pluralism(self.arches)
        arches = ', '.join(self.arches)
        return f'vulnerable via {self.glsa}, keyword{s}: {arches}'


class GlsaCheck(GentooRepoCheck):
    """Scan for vulnerable ebuilds in the tree.

    Requires a GLSA directory for vulnerability info.
    """

    known_results = frozenset([VulnerablePackage])

    @staticmethod
    def mangle_argparser(parser):
        parser.plugin.add_argument(
            "--glsa-dir", type=existent_dir, help="custom glsa directory")

    def __init__(self, *args):
        super().__init__(*args)
        glsa_dir = self.options.glsa_dir
        if glsa_dir is None:
            for repo in reversed(self.options.target_repo.trees):
                path = pjoin(repo.location, 'metadata', 'glsa')
                if os.path.isdir(path):
                    glsa_dir = path
                    break
            else:
                raise SkipOptionalCheck(self, 'no available glsa source')

        # this is a bit brittle
        self.vulns = {}
        for r in GlsaDirSet(glsa_dir):
            if len(r) > 2:
                self.vulns.setdefault(
                    r[0].key, []).append(packages.AndRestriction(*r[1:]))
            else:
                self.vulns.setdefault(r[0].key, []).append(r[1])

    def feed(self, pkg):
        for vuln in self.vulns.get(pkg.key, []):
            if vuln.match(pkg):
                arches = set()
                for v in collect_package_restrictions(vuln, ['keywords']):
                    if isinstance(v.restriction, values.ContainmentMatch2):
                        arches.update(x.lstrip('~') for x in v.restriction.vals)
                    else:
                        raise Exception(
                            f'unexpected restriction sequence- {v.restriction} in {vuln}')
                keys = {x.lstrip('~') for x in pkg.keywords if not x.startswith('-')}
                if arches:
                    arches = sorted(arches.intersection(keys))
                    assert arches
                else:
                    arches = sorted(keys)
                yield VulnerablePackage(arches, str(vuln), pkg=pkg)
