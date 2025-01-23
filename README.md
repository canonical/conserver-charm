# Conserver Charm

A Juju charm that deploys and manages [conserver](https://www.conserver.com/), a serial console management server. Conserver allows multiple users to watch a serial console at the same time.

## Configuration

The charm provides two main configuration options:

### config-file

The content for the main conserver configuration file (`/etc/conserver/conserver.cf`). This file defines:
- Console access permissions
- Console device settings
- Logging configurations
- Server behavior settings

The contents of this file must be base64 encoded before passing it to the charm.

Example configuration (see conserver documentation for more details):
```
config * {
}
default full {
  rw *;
}
default * {
  logfile /var/log/conserver/console.log;
  timestamp "1lab %Y-%m-%d %H:%M:%S";
}
##
## list of clients we allow/trust
##
access * {
  # trusted 10.0.0.2;
  allowed 10.0.0.2;
}
##
## list of consoles we serve
##
console ttyS0 {
    master localhost;
    device /dev/ttyS0;
    baud 9600;
    options local;
}

console ipmi-host {
        master localhost;
        type exec;
        exec (ipmitool -I lanplus -H 10.1.1.11 -U admin -P password sol deactivate || : && ipmitool -I lanplus -H 10.1.1.11 -U admin -P insecure sol activate);
}
```

### passwd-file

The content for the conserver password file (`/etc/conserver/conserver.passwd`), which must be base64 encoded. This file controls user access to consoles.

Example (You can use `openssl passwd -1` to generate the password hash):
```
admin:$1$iexQAX66$09labjDCDgh4hrxRXgD/r1
```

## Usage

Deploy the charm:
```bash
juju deploy conserver
```

**Note**: The charm will automatically deploy the `conserver-server` apt package, and configure it to start on boot, but it will fail to come up with the initial configuration since no connections are configured in conserver.cf by default. You'll need to configure the charm as described in this document before it can be used.

Configure with your settings:
```bash
juju config conserver config-file="$(cat your-conserver.cf | base64 -w0)"
juju config conserver passwd-file="$(cat your-conserver.passwd | base64 -w0)"
```

## More Information

- [Conserver Documentation](https://www.conserver.com/)
- [Juju SDK Documentation](https://juju.is/docs/sdk)
