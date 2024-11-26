import json
import requests
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission, check_permission

class CallLoggerApp(App):
    def build(self):
        self.title = "Call Logger"
        layout = BoxLayout(orientation='vertical')

        self.output = TextInput(hint_text='Call logs will appear here...', readonly=True, multiline=True)
        scroll_view = ScrollView(size_hint=(1, 0.9))
        scroll_view.add_widget(self.output)
        layout.add_widget(scroll_view)

        button = Button(text='Fetch Call Logs', size_hint=(1, 0.1))
        button.bind(on_press=self.fetch_call_logs)
        layout.add_widget(button)

        upload_button = Button(text='Upload Logs to GitHub', size_hint=(1, 0.1))
        upload_button.bind(on_press=self.upload_logs)
        layout.add_widget(upload_button)

        return layout

    def fetch_call_logs(self, instance):
        if platform != 'android':
            self.output.text = "This feature is only available on Android devices."
            return

        if not check_permission(Permission.READ_CALL_LOG):
            self.output.text = "Requesting permission to read call logs..."
            request_permissions([Permission.READ_CALL_LOG], self.on_permission_result)
        else:
            self.read_call_logs()

    def on_permission_result(self, permissions, results):
        if results[0]:  # Permission granted
            self.read_call_logs()
        else:
            self.output.text = "Permission to read call logs was denied."

    def read_call_logs(self):
        try:
            content_resolver = autoclass('android.content.Context').getContentResolver()
            cursor = content_resolver.query(
                autoclass('android.provider.CallLog$Calls').CONTENT_URI,
                None, None, None, None
            )

            logs = []
            while cursor.moveToNext():
                number = cursor.getString(cursor.getColumnIndex('NUMBER'))
                date = cursor.getString(cursor.getColumnIndex('DATE'))
                duration = cursor.getString(cursor.getColumnIndex('DURATION'))
                logs.append(f"Number: {number}, Date: {date}, Duration: {duration} sec")

            cursor.close()
            self.output.text = "\n".join(logs) if logs else "No call logs found."
        except Exception as e:
            self.output.text = f"Error reading call logs: {e}"

    def upload_logs(self, instance):
        logs = self.output.text
        if not logs or logs == "No call logs found.":
            self.output.text = "No logs to upload."
            return

        # Replace these with your GitHub details
        github_token = 'YOUR_GITHUB_TOKEN'
        repo_name = 'YOUR_USERNAME/YOUR_REPO_NAME'
        file_name = 'call_logs.txt'
        
        # Prepare the API request
        url = f'https://api.github.com/repos/{repo_name}/contents/{file_name}'
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Check if the file already exists
        response = requests.get(url, headers=headers)
        if response.status_code == 200:  # File exists
            sha = response.json()['sha']
            message = 'Updating call logs'
            content = logs.encode('utf-8').decode('utf-8').strip()
            data = {
                'message': message,
                'content': content,
                'sha': sha
            }
            response = requests.put(url , headers=headers, data=json.dumps(data))
        else:  # File does not exist
            message = 'Creating call logs file'
            content = logs.encode('utf-8').decode('utf-8').strip()
            data = {
                'message': message,
                'content': content
            }
            response = requests.put(url, headers=headers, data=json.dumps(data))

        if response.status_code in [201, 200]:
            self.output.text = "Logs uploaded successfully!"
        else:
            self.output.text = f"Failed to upload logs: {response.json().get('message', 'Unknown error')}"

if __name__ == '__main__':
    CallLoggerApp().run()
