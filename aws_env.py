import argparse
import io
import sys

import boto3
from jinja2 import Template


class Command(object):
    def __init__(self):
        self.ssm = boto3.client('ssm', region_name='us-east-1')

    def handle(self, args):
        path = args.path
        output = args.output
        env_vars = self.get_env_vars(path)
        buff = self.format_env_vars(env_vars, output)
        sys.stdout.write(buff.read())
        buff.close()

    def get_env_vars(self, path):
        paginator = self.ssm.get_paginator('get_parameters_by_path')
        responses = paginator.paginate(
            Path=path,
            WithDecryption=True,
        )
        env_vars = []
        for response in responses:
            parameters = response['Parameters']
            for param in parameters:
                name = param['Name']
                value = param['Value']
                env_vars.append({
                    'name': self._parse_parameter_name(name),
                    'value': value,
                })
        return env_vars

    def write_env_vars(self, filename, env_vars, output):
        with open(filename, 'w') as f:
            for obj in env_vars:
                name = obj['name']
                value = obj['value']
                if output == 'docker':
                    f.write('{}={}\n'.format(name, value))
                elif output == 'exports':
                    f.write('export {}={}\n'.format(name, value))

    def format_env_vars(self, env_vars, output):
        buff = io.StringIO()
        if output == 'docker':
            self._format_docker(buff, env_vars)
        elif output == 'exports':
            self._format_exports(buff, env_vars)
        elif output == 'elasticbeanstalk':
            self._format_elasticbeanstalk(buff, env_vars)
        buff.seek(0)
        return buff

    def _format_docker(self, buff, env_vars):
        for obj in env_vars:
            name = obj['name']
            value = obj['value']
            buff.write('{}={}\n'.format(name, value))

    def _format_exports(self, buff, env_vars):
        for obj in env_vars:
            name = obj['name']
            value = obj['value']
            buff.write('export {}={}\n'.format(name, value))

    def _format_elasticbeanstalk(self, buff, env_vars):
        j2 = (
            'option_settings\n'
            '{% for env in env_vars %}'
            ' - option_name: {{ env.name }}\n'
            '   value: "{{ env.value }}"\n'
            '{% endfor %}'
        )
        template = Template(j2)
        rendered = template.render({'env_vars': env_vars})
        buff.write(rendered)

    def _parse_parameter_name(self, name):
        i = name.rindex('/')
        return name[i + 1:]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--path', required=True,
    )
    parser.add_argument(
        '-o', '--output', default='docker', choices=['docker', 'exports', 'elasticbeanstalk']
    )
    args = parser.parse_args()
    Command().handle(args)
