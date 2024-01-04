from setuptools import setup

setup(
    name="ggg_spectra",
    description="Make plots from the spectrum files output by GGG",
    author="Sebastien Roche",
    author_email="sebastien.roche@mail.utoronto.ca",
    version="1.2.0",
    url="https://bitbucket.org/rocheseb/ggg_spectra",
    license="MIT",
    packages=["ggg_spectra"],
    package_dir={"ggg_spectra": "ggg_spectra"},
    package_data={"ggg_spectra": ["spectra/*", "save/.*", "data/*.json",]},
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    entry_points={"console_scripts": ["ggg_spectra=ggg_spectra.main:main",],},
    zip_safe=False,
    install_requires=[
        "bokeh==0.13.0",
        "jinja2==2.9.6",
        "tornado==4.5.2",
        "markupsafe==2.0.1",
        "numpy==1.14.2",
    ],
)
