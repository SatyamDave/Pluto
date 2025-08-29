# Device Bridge Pack for Pluto AI

This pack enables Pluto to control your device directly through automation tools, allowing for true "anything on your phone" functionality while maintaining the messages-only interface.

## Overview

The Device Bridge allows Pluto to:
- Toggle system settings (Wi-Fi, DND, brightness)
- Set alarms and timers
- Take photos
- Run device shortcuts
- Control apps automatically

## Security

All commands are signed with HMAC-SHA256 using your personal secret key. Only commands from Pluto with valid signatures will execute.

## Android Setup (Tasker)

### Prerequisites
- [Tasker](https://play.google.com/store/apps/details?id=net.dinglisch.android.taskerm) installed
- Tasker permissions granted (accessibility, notifications, etc.)

### Installation

1. **Import the Tasker Profile**
   - Download `android_tasker_profile.prf.xml`
   - Open Tasker → Menu → Data → Import
   - Select the downloaded file
   - Grant any requested permissions

2. **Configure Your Secret Key**
   - In Tasker, open the "Pluto Command Handler" profile
   - Edit the "Set Secret Key" task
   - Replace `your_secret_key_here` with your actual secret
   - Save the task

3. **Test the Setup**
   - Send a test command via SMS: "Turn on DND"
   - Pluto should respond with a signed command
   - Tasker should execute the action automatically

### How It Works

1. Pluto sends an SMS with a `PLUTO://cmd/...` payload
2. Tasker detects the SMS and extracts the command
3. Tasker validates the HMAC signature
4. If valid, Tasker executes the requested action
5. Tasker sends confirmation back to Pluto

### Supported Actions

- **System Settings**: `wifi`, `dnd`, `brightness`, `volume`
- **Device Control**: `alarm`, `camera`, `flashlight`
- **App Control**: `open_app`, `run_shortcut`
- **Custom Actions**: Any Tasker task you create

### Customization

You can extend the device bridge by:
1. Adding new command handlers in the "Command Router" task
2. Creating custom Tasker tasks for specific actions
3. Modifying the response format

## iOS Setup (Shortcuts)

### Prerequisites
- iOS 13+ with Shortcuts app
- Shortcuts permissions granted

### Installation

1. **Add Pluto Shortcuts**
   - Download the shortcut files from this pack
   - Open each `.shortcut` file on your iOS device
   - Tap "Add Shortcut" when prompted

2. **Configure Your Secret Key**
   - Open the "Pluto Command Handler" shortcut
   - Edit the "Set Secret Key" action
   - Replace the placeholder with your actual secret

3. **Set Up Automation (Optional)**
   - Open Shortcuts → Automation tab
   - Create new automation for "When Message Received"
   - Filter for messages from Pluto's number
   - Add action: Run Shortcut → Pluto Command Handler

### How It Works

1. Pluto sends an SMS with a `PLUTO://cmd/...` payload
2. Shortcuts detects the message (manual or automated)
3. Shortcuts validates the HMAC signature
4. If valid, Shortcuts executes the requested action
5. Shortcuts can send confirmation back to Pluto

### Supported Actions

- **System Settings**: Limited due to iOS restrictions
- **Device Control**: `alarm`, `camera`, `flashlight`
- **App Control**: `open_app`, `run_shortcut`
- **Custom Actions**: Any Shortcuts action you create

### Limitations

iOS has more restrictions than Android:
- No background automation without user interaction
- Limited system settings access
- Requires manual triggering for most actions

## Command Format

All commands follow this format:
```
PLUTO://cmd/{action}?{params}&{signature}
```

### Example Commands

```
PLUTO://cmd/wifi?state=on&signature=abc123...
PLUTO://cmd/dnd?until=18:00&signature=def456...
PLUTO://cmd/alarm?time=07:00&signature=ghi789...
```

### Parameters

- **wifi**: `state` (on/off)
- **dnd**: `until` (time), `duration` (minutes)
- **brightness**: `level` (0-100)
- **volume**: `level` (0-100)
- **alarm**: `time` (HH:MM), `label` (optional)
- **camera**: `mode` (photo/video), `flash` (on/off)

## Security Best Practices

1. **Keep Your Secret Key Private**
   - Never share your secret key
   - Use a strong, random key
   - Rotate keys periodically

2. **Validate Commands**
   - Always check HMAC signatures
   - Verify command expiration
   - Log all executed commands

3. **Limit Permissions**
   - Only grant necessary permissions
   - Review automation rules regularly
   - Monitor for unexpected actions

## Troubleshooting

### Common Issues

1. **Commands Not Executing**
   - Check Tasker/Shortcuts permissions
   - Verify secret key configuration
   - Check command format and signature

2. **Permission Errors**
   - Grant accessibility permissions
   - Enable notification access
   - Check device-specific settings

3. **Signature Validation Fails**
   - Verify secret key matches
   - Check command format
   - Ensure no message corruption

### Debug Mode

Enable debug logging by:
- **Tasker**: Set log level to Debug in preferences
- **Shortcuts**: Add "Show Result" actions to see execution flow

### Support

For device bridge issues:
1. Check the logs in Tasker/Shortcuts
2. Verify command format matches examples
3. Test with simple commands first
4. Contact Pluto support with logs

## Advanced Features

### Custom Actions

Create your own actions by:
1. Adding new command handlers
2. Creating custom Tasker tasks/Shortcuts
3. Extending the command router

### Batch Commands

Execute multiple actions with:
```
PLUTO://cmd/batch?actions=wifi:on,dnd:on&signature=...
```

### Conditional Execution

Add conditions based on:
- Time of day
- Location
- Device state
- User preferences

### Integration with Other Apps

Connect to:
- Home automation systems
- Fitness trackers
- Smart home devices
- Third-party automation tools

## Future Enhancements

- **Webhook Support**: Execute commands via HTTP
- **Push Notifications**: Real-time command delivery
- **Biometric Authentication**: Require fingerprint/face ID
- **Geofencing**: Location-based automation
- **Machine Learning**: Predict and suggest actions

## Contributing

To contribute to the device bridge:
1. Test on your device
2. Document new features
3. Share automation examples
4. Report bugs and issues

---

**Note**: The device bridge requires careful setup and testing. Start with simple commands and gradually add complexity. Always test in a safe environment before using for critical functions.
