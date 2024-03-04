from setuptools import setup, find_packages

# The following information is just for testing
setup(
    name='qsofinstr',  
    version='0.1.0',  
    author='Bob Xu',  
    author_email='jx1820@ic.ac.uk',  # Current email
    description='The test version of the quantum circuit transpiler for QSoF', 
    long_description=open('README.md').read(),  # a detailed description is in README.md
    # long_description_content_type='text/markdown',  # Optional: specify markdown for long description
    url='https://github.com/Jubo-Xu/QSoF.git',  # Optional: the URL of your package's homepage or repository
    packages=find_packages(),  # Automatically find and include all packages
    install_requires=[
        # List of dependencies required by qsofinstr
        # Currently, there are no dependencies, when optimization functionality is added, the dependencies will be added
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        # 'License :: OSI Approved :: MIT License',  # Replace with the appropriate license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6', 
    entry_points={
        # Optional: define console scripts or GUI applications
        'console_scripts': [
            'qsofinstr=qsof.CLI:main', # Path and name can be adjusted later
        ],
    },
    # Add other parameters as needed, such as package_data, include_package_data, etc later
)