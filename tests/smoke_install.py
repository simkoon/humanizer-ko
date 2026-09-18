"""Network smoke test for Skills CLI; never installs into the real home."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

VERSION = '1.7.0'


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else 'simkoon/humanizer-ko'
    if Path(source).exists():
        source = str(Path(source).resolve())
    npx = shutil.which('npx')
    if not npx:
        raise SystemExit('Node.js/npm (npx) is required.')
    with tempfile.TemporaryDirectory(prefix='humanizer-ko-install-') as temp:
        root = Path(temp)
        home, project = root / 'home', root / 'project'
        home.mkdir()
        project.mkdir()
        env = os.environ.copy()
        for key in ('HOME', 'USERPROFILE'):
            env[key] = str(home)
        for key, suffix in [('XDG_CONFIG_HOME', 'config'), ('CODEX_HOME', 'codex'),
                            ('CLAUDE_CONFIG_DIR', 'claude'), ('HERMES_HOME', 'hermes'),
                            ('npm_config_cache', 'npm-cache')]:
            env[key] = str(home / suffix)
        env.update(DISABLE_TELEMETRY='1', DO_NOT_TRACK='1', CI='1')
        command = [npx, '--yes', 'skills@' + VERSION, 'add', source]

        def run(args):
            result = subprocess.run(command + args, cwd=project, env=env,
                                    text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=180)
            print(result.stdout)
            result.check_returncode()
            return result.stdout

        output = run(['--list'])
        if 'humanizer-ko' not in output:
            raise AssertionError('Skill was not discovered')
        run(['--skill', 'humanizer-ko', '-a', 'claude-code', 'codex', '-y'])
        for relative in ('.claude/skills/humanizer-ko', '.agents/skills/humanizer-ko'):
            installed = project / relative
            if not installed.resolve().is_relative_to(root.resolve()):
                raise AssertionError('Install escaped temporary workspace')
            for name in ('SKILL.md', 'references/evidence.md', 'LICENSE', 'NOTICE.md'):
                target = installed / name
                if not target.is_file():
                    raise AssertionError('Missing installed file: ' + str(target))
                if Path(source).is_dir():
                    if target.read_bytes() != (Path(source) / name).read_bytes():
                        raise AssertionError('Installed contents differ: ' + name)
            if 'name: humanizer-ko' not in (installed / 'SKILL.md').read_text():
                raise AssertionError('Wrong skill installed')
            print('Verified:', relative)
        print('PASS: discovery and Claude Code/Codex installation; Skills CLI ' + VERSION)


if __name__ == '__main__':
    main()
