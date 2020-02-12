%global pkgname downloadmanager
%global version 1.1.0
%global release 1
%global __python /opt/se2ve/bin/python3
%global debug_package %{nil}

Name: %{pkgname}
Version: %{version}
Release: %{release}%{?dist}
Summary:	Python Downloadmanager for arbritrary files with post action
Source:     downloadmanager.tar.gz
Epoch:      1
License:	Beerware
URL:		https://gitlab.3ve.bmlv.at/se2ve/download-manager
BuildArch:  x86_64
AutoReqProv: no

%description
Python Downloadmanager for arbritrary files with post action

%prep
%setup -q -n %{name}

%build

%clean
rm -rf %{buildroot}

%install
rm -rf %{buildroot}
install -m 755 -d %{buildroot}/opt/downloadmanager/
install -m 755 -d %{buildroot}/opt/downloadmanager/manager/
install -m 755 main.py %{buildroot}/opt/downloadmanager/main.py
install -m 755 downloadmanager %{buildroot}/opt/downloadmanager/downloadmanager
install -m 644 README.md %{buildroot}/opt/downloadmanager/README.md
install -m 644 config.yaml %{buildroot}/opt/downloadmanager/config.yaml
install -m 644 manager/*.py %{buildroot}/opt/downloadmanager/manager/
cp -R .venv %{buildroot}/opt/downloadmanager/.venv/


%files
%defattr(644,rpa,rpa,755)
/opt/downloadmanager/
%attr(755,rpa,rpa)/opt/downloadmanager/main.py
%attr(755,rpa,rpa)/opt/downloadmanager/downloadmanager
%config(noreplace) /opt/downloadmanager/config.yaml
%doc README.md


