#Module-Specific definitions
%define mod_name mod_pubcookie
%define mod_conf A62_%{mod_name}.conf
%define mod_so %{mod_name}.so

Summary:	Open-source software for intra-institutional web authentication
Name:		pubcookie
Version:	3.3.3
Release:	%mkrel 2
Group:		System/Servers
License:	Apache License
URL:		http://www.pubcookie.org/
Source0:	http://www.pubcookie.org/downloads/%{name}-%{version}.tar.gz
Source1:	%{mod_conf}
Source2:	pubcookie.xinetd
Patch0:		pubcookie-DESTDIR.diff
Patch1:		pubcookie-paths.diff
Patch2:		pubcookie-3.3.0a-pki_dir.diff
Requires:	xinetd
Requires:	rootcerts
Requires:	openssl
Requires(pre): rpm-helper
Requires(postun): rpm-helper
BuildRequires:	apache-mpm-prefork >= 2.2.4
BuildRequires:	apache-devel >= 2.2.4
BuildRequires:	openssl-devel
BuildRequires:	openldap-devel
BuildRequires:	krb5-devel
BuildRequires:	libfcgi-devel
BuildRequires:	file
BuildRequires:	autoconf2.5
BuildRequires:	automake1.7
BuildRequires:	libtool
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
Pubcookie consists of a standalone login server and modules for common web
server platforms like Apache and Microsoft IIS. Together, these components can
turn existing authentication services (like Kerberos, LDAP, or NIS) into a
solution for single sign-on authentication to websites throughout an
institution.

%package -n	apache-%{mod_name}
Summary:	Open-source software for intra-institutional web authentication
Group:		System/Servers
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.2.4
Requires(pre):	apache >= 2.2.4
Requires(pre):	apache-mod_ssl >= 2.2.4
Requires(pre):	%{name} = %{version}-%{release}
Requires:	apache-conf >= 2.2.4
Requires:	apache >= 2.2.4
Requires:	apache-mod_ssl >= 2.2.4
Requires:	%{name} = %{version}-%{release}

%description -n	apache-%{mod_name}
Pubcookie consists of a standalone login server and modules for common web
server platforms like Apache and Microsoft IIS. Together, these components can
turn existing authentication services (like Kerberos, LDAP, or NIS) into a
solution for single sign-on authentication to websites throughout an
institution.

%prep

%setup -q -n %{name}-%{version}
%patch0 -p0
%patch1 -p1
%patch2 -p0

cp %{SOURCE1} %{mod_conf}
cp %{SOURCE2} pubcookie.xinetd

find . -type d -perm 0700 -exec chmod 755 {} \;
find . -type d -perm 0555 -exec chmod 755 {} \;
find . -type f -perm 0555 -exec chmod 755 {} \;
find . -type f -perm 0444 -exec chmod 644 {} \;

for i in `find . -type d -name CVS` `find . -type d -name .svn` `find . -type f -name .cvs\*` `find . -type f -name .#\*`; do
    if [ -e "$i" ]; then rm -r $i; fi >&/dev/null
done

# strip away annoying ^M
find . -type f|xargs file|grep 'CRLF'|cut -d: -f1|xargs perl -p -i -e 's/\r//'
find . -type f|xargs file|grep 'text'|cut -d: -f1|xargs perl -p -i -e 's/\r//'

%build
%serverbuild
export CFLAGS="$CFLAGS -DLDAP_DEPRECATED"

rm -f configure
libtoolize --copy --force; aclocal-1.7; autoconf

%configure2_5x \
    --enable-apache \
    --enable-login \
    --enable-default-des \
    --enable-krb5 \
    --enable-ldap \
    --enable-shadow \
    --with-fcgi=%{_prefix} \
    --with-apxs=%{_sbindir}/apxs

%make

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

install -d %{buildroot}%{_sysconfdir}/httpd/modules.d
install -d %{buildroot}%{_sysconfdir}/xinetd.d
install -d %{buildroot}%{_libdir}/apache-extramodules
install -d %{buildroot}%{_datadir}/%{name}/login_templates.default
install -d %{buildroot}%{_localstatedir}/%{name}/keys
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}/var/www/cgi-bin

%makeinstall_std PUBCOOKIE_DIR=%{_sysconfdir}/%{name}

mv %{buildroot}%{_libdir}/apache/%{mod_so} %{buildroot}%{_libdir}/apache-extramodules/

install -m0644 %{mod_conf} %{buildroot}%{_sysconfdir}/httpd/modules.d/%{mod_conf}
install -m0644 pubcookie.xinetd %{buildroot}%{_sysconfdir}/xinetd.d/%{name}

install -m0755 keyclient %{buildroot}%{_sbindir}/keyclient
install -m0755 keyserver %{buildroot}%{_sbindir}/keyserver

mv %{buildroot}%{_datadir}/%{name}/login/index.cgi %{buildroot}/var/www/cgi-bin/%{name}.cgi

# cleansing...
rm -f %{buildroot}%{_sysconfdir}/%{name}/keyclient
rm -f %{buildroot}%{_sysconfdir}/%{name}/keyserver

%post
service xinetd restart

%postun
service xinetd restart

%post -n apache-%{mod_name}
if [ -f /var/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun -n apache-%{mod_name}
if [ "$1" = "0" ]; then
    if [ -f /var/lock/subsys/httpd ]; then
	%{_initrddir}/httpd restart 1>&2
    fi
fi

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc doc/*.txt doc/*.html
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/xinetd.d/%{name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/config
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/config.login.sample
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/starter.key
%attr(0755,root,root) %{_sbindir}/keyclient
%attr(0755,root,root) %{_sbindir}/keyserver
%dir %attr(0755,root,root) %{_localstatedir}/%{name}
%dir %attr(0755,root,root) %{_localstatedir}/%{name}/keys
%{_datadir}/%{name}
%attr(0755,root,root) /var/www/cgi-bin/%{name}.cgi

%files -n apache-%{mod_name}
%defattr(-,root,root)
%doc doc/*.html doc/*.css
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0755,root,root) %{_libdir}/apache-extramodules/%{mod_so}
