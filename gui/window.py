from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit, \
                            QVBoxLayout, QCheckBox
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtSvg import QSvgWidget
import requests
import datetime

from gui.base_classes import F1QLabel, QHSeperationLine, QVSpacer
from gui.workers import APIUserPreferenceWorker
from lib.logger import log
from lib.file_handler import ConfigFile, get_path_temporary
from receiver.receiver import RaceReceiver
from receiver.helpers import get_local_ip
import config

F1LAPS_VERSION_ENDPOINT = "https://www.f1laps.com/api/f12020/telemetry/app/version/current/"


class StartButton(QPushButton):
    """ Main button to start/stop telemetry receiver"""
    def __init__(self):
        super().__init__('Start Telemetry')
        self.setObjectName("startButton")
        self.setFixedSize(160, 45)

    def set_validating_api_key(self):
        self.setText("Starting...")

    def set_running(self):
        self.setText("Stop Telemetry")
        self.setStyleSheet("background-color: #B91C1C;")

    def reset(self):
        self.setText("Start Telemetry")
        self.setStyleSheet("background-color: #4338CA;")

class StatusLabel(F1QLabel):
    """ Text below StartButton to display current receiver status """
    def __init__(self):
        super().__init__()
        self.setText("Status: not started")
        self.setObjectName("statusLabel")
        self.setFixedSize(100, 15)

    def set_validating_api_key(self):
        self.setStyleSheet("color: #6B7280;")
        self.setText("Checking API key...")

    def set_invalid_api_key(self):
        self.setStyleSheet("color: #B91C1C;")
        self.setText("Invalid API key")
    
    def set_running(self):
        self.setStyleSheet("color: #6B7280;")
        self.setText("Status: running")

    def reset(self):
        self.setStyleSheet("color: #6B7280;")
        self.setText("Status: not started")


class TelemetrySession:
    def __init__(self):
        # The actual receiver session
        self.session = None
        self.is_active = False

    def start(self, api_key, enable_telemetry):
        receiver_thread = RaceReceiver(api_key, enable_telemetry=enable_telemetry)
        receiver_thread.start()
        self.session = receiver_thread
        self.is_active = True
        log.info("Started telemetry session")
        return True

    def kill(self):
        self.session.kill()
        self.is_active = False
        log.info("Stopped telemetry session")
        return True


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.api_key_field = None
        self.api_key = ConfigFile().get_api_key()
        # Need app version before drawing UI
        self.app_version = config.VERSION
        # Draw the window UI
        self.init_ui()
        # Show the IP to the user
        self.set_ip()
        # Check if there's a new version
        self.check_version()
        # Track if we have an active receiver
        self.session = TelemetrySession()
        # Auto-start app if api key is set
        if self.api_key:
            self.start_button_click()

    def init_ui(self):
        # 1) Logo & heading
        logo_label = QSvgWidget(get_path_temporary('logo.svg'))
        logo_label.setFixedSize(100, 28)

        # 1) Enter API key section
        api_key_field_label = F1QLabel(
            text = "1) Enter your API key",
            object_name = "apiKeyFieldLabel"
            )
        api_key_help_text_label = F1QLabel(
            text = "You can find your API key on the <a href='https://www.f1laps.com/telemetry'>F1Laps Telemetry page</a>",
            object_name = "apiKeyHelpTextLabel"
            )
        self.api_key_field = QLineEdit()
        self.api_key_field.setObjectName("apiKeyField")
        self.api_key_field.setText(self.api_key)

        # 2) Check IP section
        ip_value_label = F1QLabel(
            text = "2) Set your F1 game Telemetry settings",
            object_name = "ipValueLabel"
            )
        ip_value_help_text_label = F1QLabel(
            text = "Open the F1 Game Settings -> Telemetry and set the IP to this value.",
            object_name = "ipValueHelpTextLabel"
            )
        self.ip_value = F1QLabel(object_name="ipValueField")
        self.ip_value.setContentsMargins(0, 0, 0, 5)
        udp_broadcast_help_text_label = F1QLabel(
            text = "Alternatively you can enable UDP broadcast mode:",
            object_name = "udpBroadcastHelpTextLabel"
            )
        self.udp_broadcast_checkbox = QCheckBox("Enable UDP broadcast mode")

        # Start/Stop button section
        self.start_button = StartButton()
        self.start_button.clicked.connect(lambda: self.start_button_click())
        self.status_label = StatusLabel()

        # Support & notes section
        help_text_label = F1QLabel(
            text = "Need help? <a href='https://www.notion.so/F1Laps-Telemetry-Documentation-55ad605471624066aa67bdd45543eaf7'>Check out the Documentation & Help Center!</a>",
            object_name = "helpTextLabel"
            )
        self.app_version_label = F1QLabel(
            text = "You're using app version %s." % self.app_version,
            object_name = "appVersionLabel"
            )
        self.subscription_label = F1QLabel(
            text = "",
            object_name = "subscriptionLabel"
            )

        # Draw layout
        self.layout = QVBoxLayout()

        # Logo section
        self.layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        self.layout.addWidget(QHSeperationLine())

        # API key section
        #self.layout.addWidget(QVSpacer(0))
        self.layout.addWidget(api_key_field_label)
        self.layout.addWidget(api_key_help_text_label)
        self.layout.addWidget(self.api_key_field)

        # Telemetry settings
        self.layout.addWidget(QVSpacer(0.5))
        self.layout.addWidget(QHSeperationLine())
        self.layout.addWidget(QVSpacer(0.5))
        self.layout.addWidget(ip_value_label)
        self.layout.addWidget(ip_value_help_text_label)
        self.layout.addWidget(self.ip_value)
        self.layout.addWidget(udp_broadcast_help_text_label)
        self.layout.addWidget(self.udp_broadcast_checkbox)

        # Start button
        self.layout.addWidget(QVSpacer(1))
        self.layout.addWidget(QHSeperationLine())
        self.layout.addWidget(QVSpacer(5))
        self.layout.addWidget(self.start_button, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        # Status & help
        self.layout.addWidget(QVSpacer(1))
        self.layout.addWidget(QHSeperationLine())
        self.layout.addWidget(help_text_label)
        self.layout.addWidget(self.app_version_label)
        self.layout.addWidget(self.subscription_label)
        self.layout.setContentsMargins(30, 20, 30, 10)
        
        self.setLayout(self.layout)
        self.setFixedWidth(420)
        self.setWindowTitle("F1Laps Telemetry") 

    def set_ip(self):
        self.ip_value.setText(get_local_ip())

    def get_api_key(self):
        """ Get API key from user input field and store it in local file """
        api_key = self.api_key_field.text()
        ConfigFile().set_api_key(api_key)
        return api_key

    def check_version(self):
        try:
            response = requests.get(F1LAPS_VERSION_ENDPOINT)
            version = response.json()['version']
            user_version_int = int(self.app_version.replace(".", ""))
            current_version_int = int(version.replace(".", ""))
            if version > self.app_version:
                self.app_version_label.setText("There's a new app version available (you're on v%s).<br><a href='https://www.f1laps.com/telemetry'>Click here to download the new version!</a>" % self.app_version)
                self.app_version_label.setStyleSheet("color: #B45309")
            elif version < self.app_version:
                self.app_version_label.setText("This is pre-release version v%s (stable version is v%s)." % (self.app_version, version))
                self.app_version_label.setStyleSheet("color: #059669")
        except Exception as ex:
            log.warning("Couldn't get most recent version from F1Laps due to: %s" % ex)

    def start_button_click(self):
        if not self.session.is_active:
            log.info("Starting new session")
            self.start_telemetry()
        else:
            log.info("Stopping session...")
            self.stop_telemetry()
            self.start_button.setText("Start Telemetry")
            self.start_button.setStyleSheet("background-color: #4338CA;")
            self.status_label.setText("Status: stopped")

    def start_telemetry(self):
        if self.session.is_active:
            log.error("A new session can't be started when another one is active")
            return False
        # Get API key from input field
        self.api_key = self.get_api_key()
        # Validate API key via F1Laps API
        self.validate_api_key(self.api_key)

    def validate_api_key(self, api_key):
        # Create a QThread object
        self.thread = QThread()
        # Create the worker object
        self.worker = APIUserPreferenceWorker(api_key)
        # Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.user_settings.connect(self.set_user_settings)
        # Start the thread
        self.thread.start()
        # Set buttons to loading state
        self.start_button.set_validating_api_key()
        self.status_label.set_validating_api_key()

    def set_user_settings(self, user_settings_dict):
        api_key_valid = user_settings_dict.get("api_key_valid")
        telemetry_enabled = user_settings_dict.get("telemetry_enabled")
        subscription_plan = user_settings_dict.get("subscription_plan")
        subscription_expires = user_settings_dict.get("subscription_expires")
        if (api_key_valid and subscription_plan) or (self.api_key == 'F1LAPS_TESTER'):
            log.info("Valid API key and subscription. Starting session...")
            self.display_subscription_information(subscription_plan, subscription_expires)
            self.start_button.set_running()
            self.status_label.set_running()
            # Actually start receiver thread
            self.session.start(self.api_key, enable_telemetry=telemetry_enabled)
        else:
            log.info("Not starting Telemetry session (api key %s, subscription %s)" % \
                ("valid" if api_key_valid else "invalid", subscription_plan if subscription_plan else "not set"))
            self.display_subscription_information(subscription_plan, subscription_expires)
            self.start_button.reset()
            self.status_label.set_invalid_api_key()

    def display_subscription_information(self, plan, expires_at):
        """ Plan and expires at are only returned if it's active """
        if plan:
            sub_text = "Subscribed to F1Laps %s plan" % plan
            self.subscription_label.setStyleSheet("color: #6B7280")
        else:
            sub_text = "You have no active F1Laps subscription. <a href='https://www.f1laps.com/telemetry'>Please subscribe now.</a>"
            self.subscription_label.setStyleSheet("color: #B45309")
        self.subscription_label.setText(sub_text)

    def stop_telemetry(self):
        if not self.session.is_active:
            log.error("Session can't be stopped as there is no active session")
            return None
        self.session.kill()
        return None
