EAPI=7

DESCRIPTION="Ebuild missing USE dependency default"
HOMEPAGE="https://github.com/pkgcore/pkgcheck"
SLOT="0"
LICENSE="BSD"
DEPEND="stub/stub1[foo]"
RDEPEND="|| ( stub/stub2[used] stub/stub2[-foo] )"
BDEPEND="stub/stub3[foo?]"
PDEPEND="stub/stub4[!foo?]"
