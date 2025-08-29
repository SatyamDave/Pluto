"""
Deep Link Service for Jarvis Phone AI Assistant
Generates appropriate deep links for different device types and actions
"""

import logging
import urllib.parse
from typing import Dict, Any, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DeepLinkService:
    """Service for generating deep links across different platforms"""
    
    def __init__(self):
        # Device-specific link formats
        self.device_formats = {
            "ios": {
                "call": "tel:{phone}",
                "sms": "sms:{phone}&body={message}",
                "maps": "https://maps.apple.com/?daddr={destination}",
                "alarm": "shortcuts://run-shortcut?name=SetAlarm&input={time}",
                "calendar": "calshow://",
                "messages": "messages://",
                "slack": "slack://channel?team={team}&id={channel}",
                "notion": "notion://",
                "twitter": "twitter://post?message={message}",
                "uber": "uber://?action=setPickup&pickup={pickup}&dropoff={dropoff}",
                "lyft": "lyft://ridetype?pickup={pickup}&destination={dropoff}",
                "doordash": "doordash://restaurant/{restaurant_id}",
                "camera": "camera://",
                "photos": "photos-redirect://",
                "settings": "App-Prefs://",
                "wifi": "App-Prefs://root=WIFI",
                "dnd": "App-Prefs://root=DO_NOT_DISTURB"
            },
            "android": {
                "call": "tel:{phone}",
                "sms": "smsto:{phone}:{message}",
                "maps": "geo:0,0?q={destination}",
                "alarm": "clock://",
                "calendar": "content://com.android.calendar/time/",
                "messages": "sms://",
                "slack": "slack://C{channel_id}",
                "notion": "notion://",
                "twitter": "twitter://post?message={message}",
                "uber": "uber://?action=setPickup&pickup={pickup}&dropoff={dropoff}",
                "lyft": "lyft://ridetype?pickup={pickup}&destination={dropoff}",
                "doordash": "doordash://restaurant/{restaurant_id}",
                "camera": "camera://",
                "photos": "content://media/external/images/media/",
                "settings": "android.settings://",
                "wifi": "android.settings.WIFI_SETTINGS",
                "dnd": "android.settings.ZEN_MODE_SETTINGS"
            },
            "unknown": {
                "call": "tel:{phone}",
                "sms": "sms:{phone}?body={message}",
                "maps": "https://maps.google.com/maps?q={destination}",
                "alarm": "clock://",
                "calendar": "calendar://",
                "messages": "sms://",
                "slack": "slack://",
                "notion": "notion://",
                "twitter": "twitter://",
                "uber": "uber://",
                "lyft": "lyft://",
                "doordash": "doordash://",
                "camera": "camera://",
                "photos": "photos://",
                "settings": "settings://",
                "wifi": "settings://wifi",
                "dnd": "settings://dnd"
            }
        }
    
    def generate_call_link(self, phone_number: str, device_type: str = "unknown") -> Dict[str, Any]:
        """
        Generate call deeplink
        
        Args:
            phone_number: Phone number to call
            device_type: Device type (ios, android, unknown)
            
        Returns:
            Dictionary with deeplink and metadata
        """
        try:
            # Clean phone number
            clean_phone = self._clean_phone_number(phone_number)
            
            # Get format for device
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            call_format = format_template["call"]
            
            # Generate link
            deeplink = call_format.format(phone=clean_phone)
            
            return {
                "url": deeplink,
                "label": f"📞 Call {phone_number}",
                "app_name": "Phone",
                "action": "make_call",
                "device_type": device_type
            }
            
        except Exception as e:
            logger.error(f"Error generating call link: {e}")
            return {"url": "", "label": "Call failed", "error": str(e)}
    
    def generate_sms_link(self, phone_number: str, message: str, device_type: str = "unknown") -> Dict[str, Any]:
        """
        Generate SMS deeplink
        
        Args:
            phone_number: Phone number to text
            message: Message content
            device_type: Device type (ios, android, unknown)
            
        Returns:
            Dictionary with deeplink and metadata
        """
        try:
            # Clean phone number and message
            clean_phone = self._clean_phone_number(phone_number)
            clean_message = urllib.parse.quote(message)
            
            # Get format for device
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            sms_format = format_template["sms"]
            
            # Generate link
            deeplink = sms_format.format(phone=clean_phone, message=clean_message)
            
            return {
                "url": deeplink,
                "label": f"✉️ Text {phone_number}",
                "app_name": "Messages",
                "action": "send_sms",
                "device_type": device_type,
                "prefilled_message": message
            }
            
        except Exception as e:
            logger.error(f"Error generating SMS link: {e}")
            return {"url": "", "label": "SMS failed", "error": str(e)}
    
    def generate_maps_link(self, destination: str, device_type: str = "unknown") -> Dict[str, Any]:
        """
        Generate maps deeplink
        
        Args:
            destination: Destination address/place
            device_type: Device type (ios, android, unknown)
            
        Returns:
            Dictionary with deeplink and metadata
        """
        try:
            # Clean destination
            clean_destination = urllib.parse.quote(destination)
            
            # Get format for device
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            maps_format = format_template["maps"]
            
            # Generate link
            deeplink = maps_format.format(destination=clean_destination)
            
            return {
                "url": deeplink,
                "label": f"🗺️ Directions to {destination}",
                "app_name": "Maps",
                "action": "open_maps",
                "device_type": device_type,
                "destination": destination
            }
            
        except Exception as e:
            logger.error(f"Error generating maps link: {e}")
            return {"url": "", "label": "Maps failed", "error": str(e)}
    
    def generate_alarm_link(self, time: str, device_type: str = "unknown") -> Dict[str, Any]:
        """
        Generate alarm deeplink
        
        Args:
            time: Time for alarm (e.g., "6:30 AM")
            device_type: Device type (ios, android, unknown)
            
        Returns:
            Dictionary with deeplink and metadata
        """
        try:
            # Get format for device
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            alarm_format = format_template["alarm"]
            
            # Generate link
            if device_type == "ios":
                # iOS Shortcuts format
                deeplink = alarm_format.format(time=urllib.parse.quote(time))
            else:
                # Android and others
                deeplink = alarm_format
            
            return {
                "url": deeplink,
                "label": f"⏰ Set alarm for {time}",
                "app_name": "Clock",
                "action": "set_alarm",
                "device_type": device_type,
                "alarm_time": time
            }
            
        except Exception as e:
            logger.error(f"Error generating alarm link: {e}")
            return {"url": "", "label": "Alarm failed", "error": str(e)}
    
    def generate_app_link(
        self, 
        app_name: str, 
        params: Dict[str, Any], 
        device_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Generate app deeplink
        
        Args:
            app_name: Name of the app
            params: App-specific parameters
            device_type: Device type (ios, android, unknown)
            
        Returns:
            Dictionary with deeplink and metadata
        """
        try:
            app_name_lower = app_name.lower()
            
            # Get format for device
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            
            if app_name_lower == "slack":
                return self._generate_slack_link(params, device_type)
            elif app_name_lower == "notion":
                return self._generate_notion_link(params, device_type)
            elif app_name_lower == "twitter":
                return self._generate_twitter_link(params, device_type)
            elif app_name_lower == "uber":
                return self._generate_uber_link(params, device_type)
            elif app_name_lower == "lyft":
                return self._generate_lyft_link(params, device_type)
            elif app_name_lower == "doordash":
                return self._generate_doordash_link(params, device_type)
            elif app_name_lower == "calendar":
                return self._generate_calendar_link(params, device_type)
            elif app_name_lower == "messages":
                return self._generate_messages_link(params, device_type)
            else:
                # Generic app link
                app_format = format_template.get(app_name_lower, "app://")
                deeplink = app_format.format(**params)
                
                return {
                    "url": deeplink,
                    "label": f"📱 Open {app_name}",
                    "app_name": app_name,
                    "action": "open_app",
                    "device_type": device_type
                }
                
        except Exception as e:
            logger.error(f"Error generating app link: {e}")
            return {"url": "", "label": f"Open {app_name} failed", "error": str(e)}
    
    def generate_device_action_link(
        self, 
        action: str, 
        params: Dict[str, Any], 
        device_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Generate device action deeplink
        
        Args:
            action: Device action (wifi, dnd, camera, etc.)
            params: Action parameters
            device_type: Device type (ios, android, unknown)
            
        Returns:
            Dictionary with deeplink and metadata
        """
        try:
            # Get format for device
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            action_format = format_template.get(action, "")
            
            if not action_format:
                return {"url": "", "label": f"{action} not supported", "error": "Action not supported"}
            
            # Generate link
            deeplink = action_format.format(**params)
            
            # Generate friendly label
            action_labels = {
                "wifi": "Wi-Fi",
                "dnd": "Do Not Disturb",
                "camera": "Camera",
                "photos": "Photos",
                "settings": "Settings"
            }
            
            label = action_labels.get(action, action.title())
            
            return {
                "url": deeplink,
                "label": f"⚙️ {label}",
                "app_name": "Settings",
                "action": f"toggle_{action}",
                "device_type": device_type,
                "device_action": action
            }
            
        except Exception as e:
            logger.error(f"Error generating device action link: {e}")
            return {"url": "", "label": f"{action} failed", "error": str(e)}
    
    def _generate_slack_link(self, params: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Generate Slack deeplink"""
        try:
            channel = params.get("channel", "")
            team = params.get("team", "")
            
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            slack_format = format_template["slack"]
            
            if device_type == "ios":
                deeplink = slack_format.format(team=team, channel=channel)
            else:
                # Android uses channel ID
                deeplink = slack_format.format(channel_id=channel)
            
            return {
                "url": deeplink,
                "label": f"💬 Open Slack #{channel}",
                "app_name": "Slack",
                "action": "open_slack",
                "device_type": device_type,
                "channel": channel
            }
            
        except Exception as e:
            logger.error(f"Error generating Slack link: {e}")
            return {"url": "", "label": "Slack failed", "error": str(e)}
    
    def _generate_notion_link(self, params: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Generate Notion deeplink"""
        try:
            page_id = params.get("page_id", "")
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            notion_format = format_template["notion"]
            
            deeplink = f"{notion_format}{page_id}" if page_id else notion_format
            
            return {
                "url": deeplink,
                "label": "📝 Open Notion",
                "app_name": "Notion",
                "action": "open_notion",
                "device_type": device_type
            }
            
        except Exception as e:
            logger.error(f"Error generating Notion link: {e}")
            return {"url": "", "label": "Notion failed", "error": str(e)}
    
    def _generate_twitter_link(self, params: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Generate Twitter deeplink"""
        try:
            message = params.get("message", "")
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            twitter_format = format_template["twitter"]
            
            deeplink = twitter_format.format(message=urllib.parse.quote(message)) if message else twitter_format
            
            return {
                "url": deeplink,
                "label": "🐦 Open Twitter",
                "app_name": "Twitter",
                "action": "open_twitter",
                "device_type": device_type
            }
            
        except Exception as e:
            logger.error(f"Error generating Twitter link: {e}")
            return {"url": "", "label": "Twitter failed", "error": str(e)}
    
    def _generate_uber_link(self, params: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Generate Uber deeplink"""
        try:
            pickup = params.get("pickup", "")
            dropoff = params.get("dropoff", "")
            
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            uber_format = format_template["uber"]
            
            deeplink = uber_format.format(
                pickup=urllib.parse.quote(pickup),
                dropoff=urllib.parse.quote(dropoff)
            )
            
            return {
                "url": deeplink,
                "label": "🚗 Open Uber",
                "app_name": "Uber",
                "action": "open_uber",
                "device_type": device_type,
                "pickup": pickup,
                "dropoff": dropoff
            }
            
        except Exception as e:
            logger.error(f"Error generating Uber link: {e}")
            return {"url": "", "label": "Uber failed", "error": str(e)}
    
    def _generate_lyft_link(self, params: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Generate Lyft deeplink"""
        try:
            pickup = params.get("pickup", "")
            dropoff = params.get("dropoff", "")
            
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            lyft_format = format_template["lyft"]
            
            deeplink = lyft_format.format(
                pickup=urllib.parse.quote(pickup),
                dropoff=urllib.parse.quote(dropoff)
            )
            
            return {
                "url": deeplink,
                "label": "🚗 Open Lyft",
                "app_name": "Lyft",
                "action": "open_lyft",
                "device_type": device_type,
                "pickup": pickup,
                "dropoff": dropoff
            }
            
        except Exception as e:
            logger.error(f"Error generating Lyft link: {e}")
            return {"url": "", "label": "Lyft failed", "error": str(e)}
    
    def _generate_doordash_link(self, params: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Generate DoorDash deeplink"""
        try:
            restaurant_id = params.get("restaurant_id", "")
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            doordash_format = format_template["doordash"]
            
            deeplink = doordash_format.format(restaurant_id=restaurant_id) if restaurant_id else doordash_format
            
            return {
                "url": deeplink,
                "label": "🍕 Open DoorDash",
                "app_name": "DoorDash",
                "action": "open_doordash",
                "device_type": device_type
            }
            
        except Exception as e:
            logger.error(f"Error generating DoorDash link: {e}")
            return {"url": "", "label": "DoorDash failed", "error": str(e)}
    
    def _generate_calendar_link(self, params: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Generate calendar deeplink"""
        try:
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            calendar_format = format_template["calendar"]
            
            return {
                "url": calendar_format,
                "label": "📅 Open Calendar",
                "app_name": "Calendar",
                "action": "open_calendar",
                "device_type": device_type
            }
            
        except Exception as e:
            logger.error(f"Error generating calendar link: {e}")
            return {"url": "", "label": "Calendar failed", "error": str(e)}
    
    def _generate_messages_link(self, params: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Generate messages deeplink"""
        try:
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            messages_format = format_template["messages"]
            
            return {
                "url": messages_format,
                "label": "💬 Open Messages",
                "app_name": "Messages",
                "action": "open_messages",
                "device_type": device_type
            }
            
        except Exception as e:
            logger.error(f"Error generating messages link: {e}")
            return {"url": "", "label": "Messages failed", "error": str(e)}
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number for deeplinks"""
        # Remove all non-digit characters
        clean = ''.join(filter(str.isdigit, phone))
        
        # Ensure it starts with country code
        if len(clean) == 10:
            clean = "1" + clean  # Assume US number
        elif len(clean) == 11 and clean.startswith("1"):
            pass  # Already has US country code
        else:
            # Add + prefix for international numbers
            clean = "+" + clean
        
        return clean
    
    def get_supported_actions(self, device_type: str = "unknown") -> Dict[str, Any]:
        """Get list of supported actions for a device type"""
        try:
            format_template = self.device_formats.get(device_type, self.device_formats["unknown"])
            
            return {
                "device_type": device_type,
                "supported_actions": list(format_template.keys()),
                "total_actions": len(format_template)
            }
            
        except Exception as e:
            logger.error(f"Error getting supported actions: {e}")
            return {"device_type": device_type, "supported_actions": [], "total_actions": 0}
    
    def validate_deeplink(self, deeplink: str) -> bool:
        """Validate if a deeplink is properly formatted"""
        try:
            # Basic validation - check if it's a valid URL scheme
            if deeplink.startswith(("tel:", "sms:", "smsto:", "geo:", "camera://", "photos://")):
                return True
            
            # Check for valid HTTP/HTTPS URLs
            if deeplink.startswith(("http://", "https://")):
                return True
            
            # Check for custom schemes
            if "://" in deeplink:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating deeplink: {e}")
            return False
    
    def tel_link(self, phone_number: str, device_type: str = "unknown") -> Dict[str, Any]:
        """Generate telephone deeplink (alias for generate_call_link)"""
        return self.generate_call_link(phone_number, device_type)
    
    def sms_link(self, phone_number: str, message: str = "", device_type: str = "unknown") -> Dict[str, Any]:
        """Generate SMS deeplink (alias for generate_sms_link)"""
        return self.generate_sms_link(phone_number, message, device_type)
    
    def maps_link(self, destination: str, device_type: str = "unknown") -> Dict[str, Any]:
        """Generate maps deeplink (alias for generate_maps_link)"""
        return self.generate_maps_link(destination, device_type)
    
    def app_link(self, app_name: str, params: Dict[str, Any] = None, device_type: str = "unknown") -> Dict[str, Any]:
        """Generate app deeplink (alias for generate_app_link)"""
        if params is None:
            params = {}
        return self.generate_app_link(app_name, params, device_type)
