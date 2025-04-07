# Troubleshooting Guide

## Common Issues

### Connection Problems

1. **Client Can't Connect**

   - Check network connectivity
   - Verify port is open
   - Confirm controller is running

2. **SSL Errors**
   - Verify certificate paths
   - Check certificate validity
   - Ensure matching protocols

### Service Issues

1. **Service Won't Start**

   - Check logs: `/var/log/pyvpsconnect/controller.log`
   - Verify permissions
   - Check port availability

2. **Client Disconnects**
   - Check network stability
   - Verify timeout settings
   - Monitor system resources

## Logs

Controller logs:

```bash
tail -f /var/log/pyvpsconnect/controller.log
```

Client debug mode:

```bash
python3 client.py --host controller_ip --log-level DEBUG
```
