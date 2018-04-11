# aws-env
Python utility to print parameter store values in the format of environment variables.

Current formats:
- exports: List of exported environment variables.
- docker: formatted to work with `--env-file-` flag.
- elasticbeanstalk: format for elasticbeanstalk configuration file.