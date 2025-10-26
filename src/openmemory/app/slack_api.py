from typing import Dict, List, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.secrets import get_secret


class SlackToolbox:
    """
    Comprehensive toolbox for Slack interactions.

    This toolbox provides functionality for:
    1. Processing Slack messages
    2. Formatting and sending responses
    3. Managing message threading
    4. Handling file attachments
    5. Looking up users by email
    6. Sending direct messages to users
    """

    # laszlo/uw-engine-alpha-ai-intergration
    # walter/ai-intergration

    def __init__(self, region: str = "us-east-1", secret_name: str = "prod/hvh-flock-slack"):
        """
        Initialize the Slack Toolbox with a client connection.

        Args:
            region (str): AWS region for secret retrieval
            secret_name (str): Name of the secret containing Slack token
        """
        # Setup Slack client
        secrets = get_secret(region, secret_name)
        self.slack_client = WebClient(token=secrets['SLACK_TOKEN'])

        # Default channel for fallback
        self.default_channel_id = 'C08VA2TNFSQ'

    def get_slack_user_id_by_email(self, email: str) -> Optional[str]:
        """
        Retrieves the Slack user ID for a given email address.

        Args:
            email (str): Email address of the Slack user

        Returns:
            Optional[str]: The Slack user ID if found, None otherwise

        Example:
            >>> toolbox.get_slack_user_id_by_email("user@example.com")
            "U0123456789"
        """
        try:
            # Look up user by email
            users_response = self.slack_client.users_lookupByEmail(email=email)
            if users_response and "user" in users_response and "id" in users_response["user"]:
                user_id = users_response["user"]["id"]
                print(f"Found Slack user ID for email {email}: {user_id}")
                return user_id
            else:
                print(f"User lookup response format unexpected for email {email}")
                return None
        except SlackApiError as e:
            print(f"Error looking up Slack user ID for email {email}: {e}")
            if e.response['error'] == 'users_not_found':
                print(f"No user found with email {email}")
            return None

    def send_message_to_slack_user(
            self,
            slack_user_id: str,
            message: str,
            thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends a direct message to a Slack user using their user ID.

        Args:
            slack_user_id (str): The Slack user ID to send the message to
            message (str): The message content to send
            thread_id (Optional[str]): Thread ID to include in the message

        Returns:
            Dict[str, Any]: A dictionary containing the delivery status and details

        Example:
            >>> toolbox.send_message_to_slack_user("U0123456789", "Hello there!")
            {"status": "success", "user_id": "U0123456789", "channel_id": "D0123456789"}
        """
        result = {
            "status": "failed",
            "user_id": slack_user_id,
            "error": None
        }

        try:
            # Open a direct message channel with the user
            convo_response = self.slack_client.conversations_open(users=[slack_user_id])
            if not convo_response or "channel" not in convo_response.data or "id" not in convo_response.data["channel"]:
                error_msg = "Failed to open conversation with user"
                print(error_msg)
                result["error"] = error_msg
                return result

            user_channel_id = convo_response.data["channel"]["id"]
            result["channel_id"] = user_channel_id

            # Add thread information if provided
            formatted_message = message
            if thread_id:
                formatted_message += f"\n\nThread ID: {thread_id}"
                # Add a link back to the thread if using LangGraph Studio
                link_back = f"<https://smith.langchain.com/studio/thread/{thread_id} | View in LangGraph Studio>"
                formatted_message += f"\n\n{link_back}"

            # Send the message to the user
            response = self.slack_client.chat_postMessage(
                channel=user_channel_id,
                text=formatted_message
            )

            if response and response["ok"]:
                result["status"] = "success"
                result["message_ts"] = response.get("ts")
                print(f"Message successfully sent to user {slack_user_id}")
            else:
                result["error"] = "Message sending failed"
                print(f"Failed to send message to user {slack_user_id}")

        except SlackApiError as e:
            error_msg = f"Error sending message to user {slack_user_id}: {e}"
            print(error_msg)
            result["error"] = str(e)

        return result

    def get_channel_id(self, channel_name: str) -> str:
        """
        Retrieve the Slack channel ID for a given channel name.

        Args:
            channel_name (str): Name of the Slack channel

        Returns:
            str: Channel ID if found, otherwise returns default channel ID
        """

        try:
            result = self.slack_client.conversations_list()
            for channel in result["channels"]:
                if channel["name"] == channel_name:
                    return channel["id"]

            print(f"Could not find channel with name {channel_name}. Using default channel ID: {self.default_channel_id}")
            return self.default_channel_id

        except SlackApiError as e:
            print(f"Error getting channel ID: {e}")
            print(f"Using default channel ID: {self.default_channel_id}")
            return self.default_channel_id

    def upload_file(
            self,
            file_path: str,
            channel_name: Optional[str] = None,
            file_comment: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a file to a Slack channel and return its permalink.

        Args:
            file_path (str): Path to the file to be uploaded
            channel_name (Optional[str]): Name of the Slack channel. Defaults to 'ai_dev_ground' if None
            file_comment (Optional[str]): Comment to add with the file upload

        Returns:
            Optional[str]: Permalink to the uploaded file if successful, None if upload fails
        """
        if channel_name is None:
            channel_name = 'hvh-flock-ops'

        print(f"Attempting to upload file to channel: {channel_name}")
        print(f"File path: {file_path}")

        # Get channel ID
        channel_id = self.get_channel_id(channel_name)

        try:
            # Uploading a file to a Slack channel
            load_response = self.slack_client.files_upload_v2(
                channel=channel_id,
                file=file_path,
                title="Assistant Artifact",
                initial_comment=file_comment or "Here is the file:"
            )
            file_url = load_response.get("file", {}).get("permalink")
            print(f"File uploaded successfully. URL: {file_url}")
            return file_url
        except SlackApiError as e:
            print(f"Error uploading file: {e}")
            if e.response['error'] == 'channel_not_found':
                print("The specified channel was not found. Please check the channel name/ID and bot permissions.")
            elif e.response['error'] == 'not_in_channel':
                print("The bot is not in the specified channel. Please invite the bot to the channel.")
            else:
                print(f"An unexpected error occurred: {e.response['error']}")
            return None

    def send_formatted_message(self, channel: str, message: str) -> Optional[dict]:
        """
        Send a formatted message to a Slack channel with proper formatting and blocks.

        Args:
            channel (str): Channel ID or name to send the message to
            message (str): Message content to be formatted and sent

        Returns:
            Optional[dict]: Slack API response if successful, None if sending fails

        Format:
            - Headers are formatted as "*:small_blue_diamond: Header*"
            - Content is formatted as ":small_blue_diamond: ```content```"
            - Supports nested structures in content
        """
        def format_part(part, is_header):
            if is_header:
                return f"*:small_blue_diamond: {part}*"
            else:
                return f":small_blue_diamond: ```{part}```"

        # Split the message into main parts
        main_parts = message.split(', ')
        formatted_parts = []

        for part in main_parts:
            if ': ' in part:
                header, content = part.split(': ', 1)
                formatted_parts.append(format_part(header, True))

                # Check if content is a nested structure
                if content.startswith('{') and content.endswith('}'):
                    # It's a nested structure, format it as a whole
                    formatted_parts.append(format_part(content, False))
                else:
                    formatted_parts.append(format_part(content, False))
            else:
                # If there's no ':', treat the whole part as content
                formatted_parts.append(format_part(part, False))

            formatted_parts.append('\n')

        # Join the parts
        formatted_message = ''.join(formatted_parts)

        # Prepare the blocks for formatted message
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": formatted_message
                }
            }
        ]

        try:
            # Send the message
            response = self.slack_client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=message  # Fallback text for notifications
            )
            return response
        except SlackApiError as e:
            print(f"Error sending message: {e}")
            return None
