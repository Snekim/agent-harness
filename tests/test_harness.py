import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.harness import matches_plugin_pin

ROOT = Path(__file__).resolve().parents[1]


def cli(script, *args, root=ROOT):
    return subprocess.run([sys.executable, str(root / "scripts" / f"{script}.py"), *map(str, args)],
                          capture_output=True, text=True, check=False)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_project_dry_run_and_repeat_install(self):
        args = ("--project", self.root)
        self.assertNotEqual(cli("doctor", *args).returncode, 0)
        self.assert_success(cli("install", *args, "--dry-run"))
        self.assertEqual(list(self.root.iterdir()), [])
        self.assert_success(cli("install", *args))
        frontend = self.root / ".codex" / "agents" / "frontend.toml"
        reference = self.root / ".agents/skills/api-design/references/api-guidelines.md"
        self.assertEqual(frontend.read_bytes(), (ROOT / "agents/frontend.toml").read_bytes())
        self.assertTrue(reference.read_text().strip())
        mtime = frontend.stat().st_mtime_ns
        self.assert_success(cli("install", *args))
        self.assertEqual(frontend.stat().st_mtime_ns, mtime)
        self.assert_success(cli("doctor", *args))

    def test_conflicting_file_prevents_all_writes(self):
        frontend = self.root / ".codex/agents/frontend.toml"
        frontend.parent.mkdir(parents=True)
        frontend.write_text("Existing local config\n")
        result = cli("install", "--project", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflict", result.stdout)
        self.assertEqual(frontend.read_text(), "Existing local config\n")
        self.assertEqual(list(frontend.parent.iterdir()), [frontend])
        self.assertFalse((self.root / ".agents").exists())

    def test_refuses_symlinked_project_config(self):
        project = self.root / "project"
        external = self.root / "elsewhere"
        project.mkdir()
        external.mkdir()
        (project / ".codex").symlink_to(external, target_is_directory=True)
        self.assertNotEqual(cli("install", "--project", project).returncode, 0)
        self.assertEqual(list(external.iterdir()), [])

    def test_user_install_stages_profiles_and_preserves_base_config(self):
        home, skills = self.root / "codex", self.root / "skills"
        home.mkdir()
        config = home / "config.toml"
        config.write_text('model = "local-choice"\n')
        args = ("--user", "--codex-home", home, "--skills-dir", skills)
        self.assert_success(cli("install", *args))
        self.assert_success(cli("doctor", *args))
        self.assertEqual(config.read_text(), 'model = "local-choice"\n')
        self.assertTrue((home / "architect.config.toml").is_file())
        self.assertTrue((home / "developer.config.toml").is_file())
        self.assertTrue((skills / "frontend-standard/SKILL.md").is_file())

    def test_optional_plugin_does_not_replace_existing_marketplace(self):
        home, skills = self.root / "codex", self.root / "skills"
        home.mkdir()
        config = home / "config.toml"
        original = ('[marketplaces.compound-engineering-plugin]\n'
                    'source_type = "git"\nsource = "https://example.org/plugin.git"\n')
        config.write_text(original)
        args = ("--user", "--codex-home", home, "--skills-dir", skills)
        self.assertNotEqual(cli("install", *args, "--with-plugins").returncode, 0)
        self.assertEqual(config.read_text(), original)
        self.assertFalse(skills.exists())

    def test_optional_plugin_refuses_symlinked_config(self):
        home, skills = self.root / "codex", self.root / "skills"
        home.mkdir()
        external = self.root / "external.toml"
        external.write_text('model = "local-choice"\n')
        (home / "config.toml").symlink_to(external)
        args = ("--user", "--codex-home", home, "--skills-dir", skills)
        result = cli("install", *args, "--with-plugins")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflict: compound-engineering", result.stdout)
        self.assertEqual(external.read_text(), 'model = "local-choice"\n')
        self.assertFalse(skills.exists())

    def test_plugin_pin_detects_edits_and_allows_codex_to_omit_symlinks(self):
        skill = self.root / "SKILL.md"
        skill.write_text("Locked skill instructions\n")
        symlink = self.root / "alias.md"
        symlink.symlink_to(skill.name)

        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.root), *args], text=True)

        git("init", "--quiet")
        git("add", "--", skill.name, symlink.name)
        git("-c", "user.name=Harness Test", "-c", "user.email=harness@example.invalid",
            "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
            "commit", "--quiet", "-m", "Lock plugin fixture")
        revision = git("rev-parse", "HEAD").strip()

        symlink.unlink()
        self.assertTrue(matches_plugin_pin(self.root, revision))
        skill.write_text("Changed instructions\n")
        self.assertFalse(matches_plugin_pin(self.root, revision))

    def test_doctor_reports_missing_manifest_files(self):
        source = self.root / "source"
        source.mkdir()
        for folder in ("agents", "profiles", "skills", "scripts"):
            shutil.copytree(ROOT / folder, source / folder, ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("harness.yaml", "harness.lock.yaml"):
            shutil.copyfile(ROOT / name, source / name)
        (source / "agents/frontend.toml").unlink()
        (source / "skills/backend-standard/SKILL.md").unlink()
        result = cli("doctor", root=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("agents/frontend.toml", result.stderr)
        self.assertIn("skills/backend-standard/SKILL.md", result.stderr)


if __name__ == "__main__":
    unittest.main()
