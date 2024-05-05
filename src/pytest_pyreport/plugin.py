import json
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader
import os
import matplotlib.pyplot as plt
import requests
from logstyle.base import CustomLog

custom_logger = CustomLog("MyLogger")


def pytest_addoption(parser):
    parser.addoption(
        '--pyreport',
        action='store_true',
        help='Generate an HTML test report'
    )
    parser.addoption(
        '--telegram-pyreport',
        nargs=2,
        metavar=('CHAT_ID', 'BOT_TOKEN'),
        help='Send the report to Telegram with the provided Chat ID and Bot Token'
    )
    parser.addoption(
        '--slack-pyreport',
        nargs=3,
        metavar=('WEBHOOK_URL', 'CHANNEL', 'BOT_TOKEN'),
        help='Send the report to Slack with the provided Webhook URL, Channel and Bot Token'
    )
    parser.addoption(
        '--server',
        help='URL or server address to include in the report notification'
    )
    parser.addoption(
        '--failed-tests-count',
        action='store_true',
        help='Output the count of failed tests to JSON file'
    )


def generate_and_save_chart(report_data):
    report_name = "PyReport"

    num_tests = len(report_data['test_cases'])
    num_failures = len([test_case for test_case in report_data['test_cases'] if test_case['result'] == 'fail'])
    num_skipped = len([test_case for test_case in report_data['test_cases'] if test_case['result'] == 'skip'])

    labels = []
    sizes = []
    explode = []
    colors = []

    if num_tests - num_failures - num_skipped > 0:
        labels.append(f'Pass ({num_tests - num_failures - num_skipped})')
        sizes.append(num_tests - num_failures - num_skipped)
        explode.append(0.1)
        colors.append('#4CAF50')

    if num_failures > 0:
        labels.append(f'Fail ({num_failures})')
        sizes.append(num_failures)
        explode.append(0.1)
        colors.append('red')

    if num_skipped > 0:
        labels.append(f'Skip ({num_skipped})')
        sizes.append(num_skipped)
        explode.append(0.1)
        colors.append('#FFA500')

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, colors=colors, startangle=140, explode=explode, autopct='%1.1f%%')
    ax.axis('equal')
    plt.title(f'{report_name} Test Results', fontsize=20, color='#333', fontweight='bold', pad=20)

    ax.legend(labels, loc="best", fontsize=14, title="Test Results", title_fontsize=14)
    ax.title.set_fontsize(20)

    ax.set_facecolor('#f2f2f2')
    fig.patch.set_facecolor('#f2f2f2')

    plt.text(0.9, -0.1, 'https://github.com/ToghrulMirzayev/pytest-pyreport', fontsize=12, color='blue', va='bottom',
             ha='right', transform=ax.transAxes)

    plt.savefig('test_results.png', dpi=300)


def load_report_data():
    with open('test_report.json', 'r') as json_file:
        report_data = json.load(json_file)
    return report_data


def pytest_sessionfinish(session):
    config = session.config
    generate_html_report = config.getoption('--pyreport')
    telegram_config = config.getoption('--telegram-pyreport')
    slack_config = config.getoption('--slack-pyreport')
    server = config.getoption('--server')
    fail_percentage_counter = config.getoption('--failed-tests-count')

    if generate_html_report:
        tree = ET.parse('result.xml')
        root = tree.getroot()

        testsuite = root.find('testsuite')
        total_time = float(testsuite.get('time'))

        test_cases = []
        for testcase in testsuite.iter('testcase'):
            test_case = {
                'name': testcase.get('name'),
                'result': 'pass',
                'details': '',
                'time': float(testcase.get('time'))
            }
            failure = testcase.find('failure')
            if failure is not None:
                test_case['result'] = 'fail'
                test_case['details'] = failure.text
            skipped = testcase.find('skipped')
            if skipped is not None:
                test_case['result'] = 'skip'
                test_case['details'] = skipped.text
            test_cases.append(test_case)

        num_tests = len(test_cases)
        num_failures = len([test_case for test_case in test_cases if test_case['result'] == 'fail'])
        num_skipped = len([test_case for test_case in test_cases if test_case['result'] == 'skip'])

        report_data = {
            'num_tests': num_tests,
            'num_failures': num_failures,
            'num_skipped': num_skipped,
            'test_cases': test_cases,
            'total_time': total_time
        }

        with open('test_report.json', 'w') as json_file:
            json.dump(report_data, json_file)

        generate_and_save_chart(report_data)

        if generate_html_report:
            package_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(package_dir, 'templates')
            env = Environment(loader=FileSystemLoader(templates_dir))
            template = env.get_template('template.html')

            html_output = template.render(test_cases=test_cases, num_tests=num_tests, num_failures=num_failures,
                                          num_skipped=num_skipped, total_time=total_time)

            with open('pyreport.html', 'w') as f:
                f.write(html_output)

            custom_logger.box_log("HTML Report generation complete", CustomLog.COLOR_GREEN)

        if fail_percentage_counter:
            fail_percentage = (num_failures / num_tests) * 100

            fail_percentage_data = {
                "fail_count": num_failures,
                "fail_percentage": fail_percentage
            }

            with open('fail_percentage.json', 'w') as json_file:
                json.dump(fail_percentage_data, json_file)

        if telegram_config and server:
            chat_id, bot_token = telegram_config
            server_url = server
            send_report_to_telegram(chat_id, bot_token, server_url)
        elif telegram_config:
            chat_id, bot_token = telegram_config
            send_report_to_telegram(chat_id, bot_token)

        if slack_config and server:
            webhook, channel, slack_bot_token = slack_config
            server_url = server
            send_report_to_slack(webhook_url=webhook, channel=channel, bot_token=slack_bot_token, server=server_url)
        elif slack_config:
            webhook, channel, slack_bot_token = slack_config
            send_report_to_slack(webhook_url=webhook, channel=channel, bot_token=slack_bot_token)


def send_report_to_telegram(chat_id, bot_token, server=None):
    report_data = load_report_data()
    generate_and_save_chart(report_data)

    if server:
        message = f"Test results are ready and available at the following URL: {server}"
    else:
        message = f"Test results are ready and available in the 'pyreport.html' file in the project directory."

    telegram_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = {'chat_id': chat_id, 'text': message}
    response = requests.post(telegram_url, data=data)

    if response.status_code == 200:
        custom_logger.box_log("Report message has been sent to Telegram chat", CustomLog.COLOR_GREEN)
    else:
        custom_logger.box_log("Error while sending report message", CustomLog.COLOR_RED)

    telegram_url_img = f'https://api.telegram.org/bot{bot_token}/sendPhoto'
    with open('test_results.png', 'rb') as photo:
        files = {'photo': ('test_results.png', photo)}
        data = {'chat_id': chat_id}
        response = requests.post(telegram_url_img, data=data, files=files)

    if response.status_code == 200:
        custom_logger.box_log("Report image has been sent to Telegram chat", CustomLog.COLOR_GREEN)
    else:
        custom_logger.box_log("Error while sending report image", CustomLog.COLOR_RED)


def send_report_to_slack(webhook_url, channel, bot_token, server=None):
    report_data = load_report_data()
    generate_and_save_chart(report_data)

    if server:
        message = f":pencil: | Test results are ready and available at the following link: {server}"
    else:
        message = f":pencil: | Test results are ready and available in the 'pyreport.html' " \
                  f"file in the project directory."

    url = "https://slack.com/api/files.upload"
    token = bot_token
    channels = channel

    files = {'file': open('test_results.png', 'rb')}
    headers = {
        'Authorization': f'Bearer {token}'
    }

    data = {'channels': channels}

    response = requests.post(url, headers=headers, data=data, files=files)
    file_url = response.json()["file"]["url_private"]

    payload = {
        "attachments": [
            {
                "text": message,
                "image_url": file_url
            }
        ]
    }

    response = requests.post(webhook_url, json=payload)

    if response.status_code == 200:
        custom_logger.box_log("Report message and image have been sent to Slack channel", CustomLog.COLOR_GREEN)
    else:
        custom_logger.box_log("Error while sending report message and image to Slack channel", CustomLog.COLOR_RED)
