[Public]
Object=(Name=IpDrv.UpdateServerCommandlet,Class=Class,MetaClass=Core.Commandlet)
Object=(Name=IpDrv.MasterServerCommandlet,Class=Class,MetaClass=Core.Commandlet)
Object=(Name=IpDrv.CompressCommandlet,Class=Class,MetaClass=Core.Commandlet)
Object=(Name=IpDrv.DecompressCommandlet,Class=Class,MetaClass=Core.Commandlet)
Object=(Name=IpDrv.TcpNetDriver,Class=Class,MetaClass=Engine.NetDriver)
Object=(Name=IpDrv.UdpBeacon,Class=Class,MetaClass=Engine.Actor)
Preferences=(Caption="Gra sieciowa TCP/IP",Parent="Networking",Class=IpDrv.TcpNetDriver)
Preferences=(Caption="Sygnał serwera LAN",Parent="Networking",Class=IpDrv.UdpBeacon,Immediate=True)

[TcpNetDriver]
ClassCaption=Gra sieciowa TCP/IP

[UdpBeacon]
ClassCaption=Sygnał serwera LAN

[DecompressCommandlet]
HelpCmd=decompress
HelpWebLink="https://www.oldunreal.com/wiki/index.php?title=Commandlet"
HelpOneLiner="Decompress a file compressed with ucc compress."
HelpUsage="decompress CompressedFile"
HelpParm[0]="CompressedFile"
HelpDesc[0]="The.uz file to decompress."

[CompressCommandlet]
HelpCmd=compress
HelpWebLink="https://www.oldunreal.com/wiki/index.php?title=Commandlet"
HelpOneLiner="Compress an Unreal package for auto-downloading. A file with extension.uz will be created."
HelpUsage="compress File1 [File2 [File3...]]"
HelpParm[0]="Files"
HelpDesc[0]="The wildcard or file names to compress."

[MasterServerUplink]
MSUPropText[0]=Reklamuj serwer
MSUPropText[1]=Przetwarzaj statystyki
MSUPropText[2]="Ignoruj bany komisyjne"
MSUPropDesc[0]=w wypadku zaznaczenia twój serwer będzie reklamowany w przeglądarce serwerów internetowych.
MSUPropDesc[1]=Publikuje statystyki graczy z twojego serwera na stronie statystyk UT2004.
MSUPropDesc[2]="Włącz, aby twój serwer pozwalał na grę graczom zbanowanym przez Komisję na serwerze głównym."
