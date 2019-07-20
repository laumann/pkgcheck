from pkgcheck.checks import python

from .. import misc


class TestPythonReport(misc.ReportTestCase):

    check = python.PythonReport(None)
    check_kls = python.PythonReport

    def mk_pkg(self, **kwargs):
        kwargs['EAPI'] = '7'
        return misc.FakePkg("app-foo/bar-1", data=kwargs)

    def test_missing_eclass_depend(self):
        self.assertNoReport(self.check,
                self.mk_pkg(_eclasses_=['python-any-r1'],
                            DEPEND='dev-lang/python'))
        self.assertNoReport(self.check,
                self.mk_pkg(DEPEND='dev-foo/frobnicate'))

        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(DEPEND='dev-lang/python')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(DEPEND='dev-lang/python:2.7')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(DEPEND='dev-lang/python:*')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(DEPEND='=dev-lang/python-2*')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(DEPEND='|| ( dev-lang/python:2.7 dev-lang/python:3.6 )')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(DEPEND='dev-python/pypy')),
            python.MissingPythonEclass)

    def test_missing_eclass_bdepend(self):
        self.assertNoReport(self.check,
                self.mk_pkg(_eclasses_=['python-any-r1'],
                            BDEPEND='dev-lang/python'))
        self.assertNoReport(self.check,
                self.mk_pkg(BDEPEND='dev-foo/frobnicate'))

        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(BDEPEND='dev-lang/python')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(BDEPEND='dev-lang/python:2.7')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(BDEPEND='dev-lang/python:*')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(BDEPEND='=dev-lang/python-2*')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(BDEPEND='|| ( dev-lang/python:2.7 dev-lang/python:3.6 )')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(BDEPEND='dev-python/pypy')),
            python.MissingPythonEclass)

    def test_missing_eclass_rdepend(self):
        self.assertNoReport(self.check,
                self.mk_pkg(_eclasses_=['python-r1'],
                            RDEPEND='dev-lang/python:2.7'))
        self.assertNoReport(self.check,
                self.mk_pkg(_eclasses_=['python-single-r1'],
                            RDEPEND='dev-lang/python:2.7'))
        self.assertNoReport(self.check,
                self.mk_pkg(RDEPEND='dev-foo/frobnicate'))

        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(RDEPEND='dev-lang/python')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(RDEPEND='dev-lang/python:2.7')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(RDEPEND='dev-lang/python:=')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(RDEPEND='=dev-lang/python-2*')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(RDEPEND='|| ( dev-lang/python:2.7 dev-lang/python:3.6 )')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(RDEPEND='dev-python/pypy')),
            python.MissingPythonEclass)

    def test_missing_eclass_pdepend(self):
        self.assertNoReport(self.check,
                self.mk_pkg(_eclasses_=['python-r1'],
                            PDEPEND='dev-lang/python:2.7'))
        self.assertNoReport(self.check,
                self.mk_pkg(_eclasses_=['python-single-r1'],
                            PDEPEND='dev-lang/python:2.7'))
        self.assertNoReport(self.check,
                self.mk_pkg(PDEPEND='dev-foo/frobnicate'))

        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(PDEPEND='dev-lang/python')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(PDEPEND='dev-lang/python:2.7')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(PDEPEND='dev-lang/python:=')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(PDEPEND='=dev-lang/python-2*')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(PDEPEND='|| ( dev-lang/python:2.7 dev-lang/python:3.6 )')),
            python.MissingPythonEclass)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(PDEPEND='dev-python/pypy')),
            python.MissingPythonEclass)

    def test_valid_packages(self):
        self.assertNoReport(self.check,
                self.mk_pkg(_eclasses_=['python-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_targets_python3_6',
                            REQUIRED_USE='|| ( python_targets_python2_7 '
                                         '     python_targets_python3_6 )'))
        # python-single-r1 with one implementation does not use PST
        self.assertNoReport(self.check,
                self.mk_pkg(_eclasses_=['python-single-r1'],
                            IUSE='python_targets_python2_7',
                            REQUIRED_USE='python_targets_python2_7'))
        self.assertNoReport(self.check,
                self.mk_pkg(_eclasses_=['python-single-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_targets_python3_6 '
                                 'python_single_target_python2_7 '
                                 'python_single_target_python3_6',
                            REQUIRED_USE='^^ ( python_single_target_python2_7 '
                                         '     python_single_target_python3_6 ) '
                                         'python_single_target_python2_7? ( '
                                         '  python_targets_python2_7 ) '
                                         'python_single_target_python3_6? ( '
                                         '  python_targets_python3_6 )'))

    def test_single_use_mismatch(self):
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(_eclasses_=['python-single-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_targets_python3_6 '
                                 'python_single_target_python2_7',
                            REQUIRED_USE='python_single_target_python2_7 '
                                         'python_single_target_python2_7? ( '
                                         '  python_targets_python2_7 )')),
            python.PythonSingleUseMismatch)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(_eclasses_=['python-single-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_single_target_python2_7 '
                                 'python_single_target_python3_6',
                            REQUIRED_USE='^^ ( python_single_target_python2_7 '
                                         '  python_single_target_python3_6 )')),
            python.PythonSingleUseMismatch)

    def test_missing_required_use(self):
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(_eclasses_=['python-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_targets_python3_6')),
            python.PythonMissingRequiredUSE)
        # incomplete REQUIRED_USE (e.g. use of python_gen_useflags)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(_eclasses_=['python-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_targets_python3_6',
                            REQUIRED_USE='|| ( python_targets_python2_7 )')),
            python.PythonMissingRequiredUSE)
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(_eclasses_=['python-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_targets_python3_6 '
                                 'python_targets_python3_7',
                            REQUIRED_USE='|| ( python_targets_python3_6 '
                                         '  python_targets_python3_7 )')),
            python.PythonMissingRequiredUSE)

        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(_eclasses_=['python-single-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_targets_python3_6 '
                                 'python_single_target_python2_7 '
                                 'python_single_target_python3_6')),
            python.PythonMissingRequiredUSE)
        # incomplete REQUIRED_USE
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(_eclasses_=['python-single-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_targets_python3_6 '
                                 'python_single_target_python2_7 '
                                 'python_single_target_python3_6',
                            REQUIRED_USE='^^ ( python_single_target_python2_7 )')),
            python.PythonMissingRequiredUSE)
        # || instead of ^^ in python-single-r1
        assert isinstance(
            self.assertReport(self.check,
                self.mk_pkg(_eclasses_=['python-single-r1'],
                            IUSE='python_targets_python2_7 '
                                 'python_targets_python3_6 '
                                 'python_single_target_python2_7 '
                                 'python_single_target_python3_6',
                            REQUIRED_USE='|| ( python_targets_python2_7 '
                                         '  python_targets_python3_6 )')),
            python.PythonMissingRequiredUSE)
