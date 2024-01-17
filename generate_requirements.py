# Standard Library
import argparse
from subprocess import check_call

VERSION_MAPPING = {
    '3.8': {
        'env_name': 'py38',
    },
    '3.9': {
        'env_name': 'py39',
    },
    '3.10': {
        'env_name': 'py310',
    },
    '3.11': {
        'env_name': 'py311',
    },
}


def main() -> None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        '--bootstrap',
        action='store_true',
        help='Bootstrap the virtual environments',
    )
    args = arg_parser.parse_args()
    for version, env_config in VERSION_MAPPING.items():
        env_name = env_config['env_name']
        pip = env_config.get('pip', 'pip')
        if args.bootstrap:
            check_call([
                'py', '-' + version,
                '-m', 'pip',
                'install',
                '--upgrade',
                pip,
                'pip-tools',
                'setuptools',
                'wheel',
            ])
        check_call([
            'py', '-' + version,
            '-m', 'piptools',
            'compile',
            '--annotate',
            '--header',
            '--no-emit-index-url',
            '--no-emit-trusted-host',
            '--output-file', 'requirements.{}.txt'.format(env_name),
            'requirements-dev.txt'
        ])


if __name__ == '__main__':
    main()
