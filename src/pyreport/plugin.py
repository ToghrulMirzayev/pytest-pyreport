import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader
import os


def pytest_addoption(parser):
    parser.addoption(
        '--pyreport',
        action='store_true',
        help='generate an HTML test report'
    )


def pytest_sessionfinish(session):
    if session.config.getoption('--pyreport'):
        try:
            with open('result.xml', 'r'):
                pass
        except FileNotFoundError:
            print('The results file does not exist.')
            return

        tree = ET.parse('result.xml')
        root = tree.getroot()

        test_cases = []
        for testcase in root.iter('testcase'):
            test_case = {
                'name': testcase.get('name'),
                'result': 'pass',
                'details': ''
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

        package_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(package_dir, 'templates')
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template('template.html')

        html_output = template.render(test_cases=test_cases, num_tests=num_tests, num_failures=num_failures,
                                      num_skipped=num_skipped)

        with open('pyreport.html', 'w') as f:
            f.write(html_output)
