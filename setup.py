from setuptools import setup, find_packages

setup(
    name='pytest-pyreport',
    version='1.0.1',
    description='PyReport is a lightweight reporting plugin for Pytest that provides concise HTML report',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Toghrul Mirzayev',
    author_email='togrul.mirzoev@gmail.com',
    url='https://github.com/ToghrulMirzayev/pytest-pyreport',
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "pytest_pyreport": ["plugin.py", "templates/template.html"],
    },
    entry_points={"pytest11": ["pytest_pyreport = pytest_pyreport.plugin"]},
    classifiers=["Framework :: Pytest",
                 "Operating System :: OS Independent",
                 "License :: OSI Approved :: MIT License",
                 "Programming Language :: Python :: 3",
                 "Topic :: Software Development :: Testing"],
    keywords='pytest_pyreport, python, pytest, report',
    install_requires=[
        'Jinja2>=3.1.2',
        'pytest>=7.3.1',
    ],
    python_requires='>=3.8',
    license='MIT'
)
