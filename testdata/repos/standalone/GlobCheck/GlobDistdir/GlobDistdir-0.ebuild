DESCRIPTION="Ebuild with unsafe glob around DISTDIR"
HOMEPAGE="https://github.com/pkgcore/pkgcheck"
SLOT="0"
LICENSE="BSD"

src_install() {
	doins "${DISTDIR}"/foo-*.bar # bad
	doins "${DISTDIR}"/"${DISTDIR}"/foo-?.bar # bad
	doins "${DISTDIR}"/foo-?-*.bar # bad

	doins "${T}"/foo-*.bar # not unsafe dir
	doins "${DISTDIR}"/foo-1.bar # no glob
	doins "${DISTDIR}"/"foo-*.bar" # quoted
	doins "${DISTDIR}"/'foo-*.bar' # quoted
}
