"""Pruebas de los bloqueos: cada bloqueo bloquea y lo de todos los días pasa.

Corren con: python3 .claude/hooks/test_bloqueos.py
Además de llamar a `motivo`, cada grupo pasa al menos un caso por el programa entero
(stdin y código de salida 2), que es como lo llama el harness.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import bloqueos  # noqa: E402

HOOK = os.path.join(os.path.dirname(__file__), 'bloqueos.py')
RDS = 'app.abc123.us-east-1.rds.amazonaws.com'


def correr(comando, cwd='.'):
    entrada = json.dumps({'tool_name': 'Bash', 'tool_input': {'command': comando}, 'cwd': cwd})
    return subprocess.run([sys.executable, HOOK], input=entrada, capture_output=True, text=True)


def repo_en(rama):
    d = tempfile.mkdtemp()
    subprocess.run(['git', 'init', '-q', '-b', rama, d], check=True)
    return d


class Push(unittest.TestCase):
    def test_push_a_rama_protegida_se_bloquea(self):
        for c in ['git push origin integracion', 'git push origin produccion', 'git push origin HEAD:integracion',
                  'git push origin desarrollo:produccion', 'git push -u origin refs/heads/produccion',
                  'git push --force origin +integracion', 'git push --all origin', 'git -C backend push origin integracion',
                  'cd x && git push origin integracion']:
            self.assertIsNotNone(bloqueos.motivo(c), c)

    def test_push_sin_rama_desde_protegida_se_bloquea(self):
        d = repo_en('integracion')
        self.assertIsNotNone(bloqueos.motivo('git push', cwd=d))
        self.assertIsNotNone(bloqueos.motivo('git push origin', cwd=d))
        self.assertIsNone(bloqueos.motivo('git push', cwd=repo_en('desarrollo')))

    def test_push_a_desarrollo_y_ramas_de_agente_pasa(self):
        for c in ['git push origin desarrollo', 'git push -q origin desarrollo', 'git push origin agente/arreglo-firma',
                  'git push -u origin HEAD:agente/produccion-ui']:
            self.assertIsNone(bloqueos.motivo(c), c)

    def test_el_programa_sale_con_2(self):
        r = correr('git push origin produccion')
        self.assertEqual(r.returncode, 2)
        self.assertIn('líder del proyecto', r.stderr)
        self.assertEqual(correr('git push origin desarrollo').returncode, 0)


class MergeDePR(unittest.TestCase):
    def test_merge_de_pr_se_bloquea(self):
        for c in ['gh pr merge 123 --squash', 'gh pr merge --admin', 'gh api -X PUT repos/org/repo/pulls/12/merge']:
            self.assertIsNotNone(bloqueos.motivo(c), c)
        self.assertEqual(correr('gh pr merge 5').returncode, 2)

    def test_ver_y_crear_pr_pasa(self):
        for c in ['gh pr view 12', 'gh pr create --base desarrollo --title x --body y', 'gh pr list']:
            self.assertIsNone(bloqueos.motivo(c), c)


class Produccion(unittest.TestCase):
    def test_psql_a_produccion_sin_solo_lectura_se_bloquea(self):
        for c in [f'psql -h {RDS} -U app -d app -c "delete from items"',
                  f'PGOPTIONS="-c statement_timeout=30000" psql -h {RDS} -d app',
                  f'DATABASE_URL=postgresql://u@{RDS}/app npx prisma migrate deploy']:
            self.assertIsNotNone(bloqueos.motivo(c), c)
        self.assertEqual(correr(f'psql -h {RDS} -d app -c "update items set nombre=1"').returncode, 2)

    def test_reabrir_la_escritura_se_bloquea(self):
        base = f"export PGOPTIONS='-c default_transaction_read_only=on'; psql -h {RDS} -d app -c "
        for sql in ['"begin read write; delete from items; commit"',
                    '"set default_transaction_read_only = off; delete from items"',
                    '"set session characteristics as transaction read write"']:
            self.assertIsNotNone(bloqueos.motivo(base + sql), sql)

    def test_lectura_en_solo_lectura_y_la_base_local_pasan(self):
        self.assertIsNone(bloqueos.motivo(f"PGOPTIONS='-c default_transaction_read_only=on' psql -h {RDS} -d app -c 'select 1'"))
        self.assertIsNone(bloqueos.motivo('psql -h localhost -U app -d app -c "delete from items"'))
        self.assertIsNone(bloqueos.motivo('docker compose exec postgres psql -U app app -c "truncate items"'))


class Entrada(unittest.TestCase):
    def test_otras_herramientas_y_entrada_rota_pasan(self):
        r = subprocess.run([sys.executable, HOOK], input='no es json', capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        r = subprocess.run([sys.executable, HOOK], input=json.dumps({'tool_name': 'Read', 'tool_input': {}}), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main(verbosity=1)
