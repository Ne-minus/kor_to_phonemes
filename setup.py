import setuptools

setuptools.setup(name='IPAkor',
                 version='2.5.4',
                 packages=['IPAkor'],
                 package_data={'IPAkor': ['static/final_trans.csv']},
                 classifiers=[
                     'Programming Language :: Python :: 3',
                     'Operating System :: OS Independent',
                     'Topic :: Scientific/Engineering'
                 ],
                 install_requires=['konlpy', 'wget'],
                 python_requires='>=3',
                 author_email='neminova2.0@gmail.com'
                 )
