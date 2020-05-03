Changelog
=========

0.2.0 (2020-05-03)
------------------
c51f2c8 - (HEAD -> master, origin/master, origin/HEAD) Fix invoke release <Darren Weber>
7350e96 - Merge pull request #5 from dazza-codes/aws-lambda <Darren Weber>
b7cd8f2 - Add terraform specs for AWS deployments <Darren Weber>
41a5411 - Merge pull request #3 from dazza-codes/tweaks <Darren Weber>
69dff9a - Fix minor lints and things <Darren Weber>
aea5c8a - Merge pull request #1 from dazza-codes/adaptations <Darren Weber>
a275f38 - Adapt to poetry package manager <Darren Weber>
eed9b2b - (upstream-aws-app/master, origin/upstream-aws-master, upstream-aws-master) readme.md <iwpnd>
edd4cf5 - now explicitly build an API to avoid a bug in SAM that creates Stage /Stage on implicit builds <iwpnd>
c0fe715 - remove uvicorn from requirements as it is not necessary for the lambda itself <iwpnd>
79ec1f1 - intendation error in Outputs in template.yml <iwpnd>
bf27cb1 - set enable_lifespan=False for Mangum adapter as it doesnt have effect in AWS Lambda <iwpnd>
a7a0e9b - depending on the execution environment either enable or disable lifespan support <iwpnd>
fa4fe0d - updated dockerfile and requirements <iwpnd>
4dabb8c - fixed trailing slash in example.py endpoints that caused redirects and failing tests. added test for example endpoint <iwpnd>
6dab260 - added example app endpoints, config, router and models <iwpnd>
2f1d461 - added example app endpoints, config, router and models <iwpnd>
6136839 - added example .travis.yml <iwpnd>
39d9693 - added example sam template <iwpnd>
3b2c26b - removed poetry. add requirements.txt and setup.py instead. also added scripts folder for example.ipynb <iwpnd>
94aa4d6 - added example pyproject.toml <iwpnd>
561456a - Added LICENCE <iwpnd>
102c428 - added Dockerfile <iwpnd>
1ad39e6 - added gitignore <iwpnd>
f48bbc2 - added pre-commit-config <iwpnd>
785620a - initial commit <iwpnd>
6dacb1b - Initial commit <Ben>

0.1.0 (2020-01-21)
------------------
- Initial example release
