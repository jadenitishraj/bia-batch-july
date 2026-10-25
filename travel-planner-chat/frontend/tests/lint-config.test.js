// @vitest-environment node
import { ESLint } from 'eslint';
import { expect, test } from 'vitest';

const eslint = new ESLint();

async function ruleIds(code) {
  const [result] = await eslint.lintText(code, { filePath: 'src/lint-example.js' });
  return result.messages.map((message) => message.ruleId);
}

test.each([
  ['eqeqeq', 'export const same = (value) => value == 1;'],
  ['curly', 'export function check(value) { if (value) return true; return false; }'],
  ['no-eval', 'export const run = (code) => eval(code);'],
  ['no-var', 'var name = "trip"; export { name };'],
  ['no-param-reassign', 'export function change(trip) { trip.title = "changed"; }'],
  ['max-lines', '// comment\n'.repeat(151)],
])('rejects violations of %s', async (rule, code) => {
  expect(await ruleIds(code)).toContain(rule);
});

test('accepts readable small modules with explicit control flow', async () => {
  const code = `export function hasDestination(trip) {
    if (trip.destination === '') {
      return false;
    }
    return true;
  }`;
  expect(await ruleIds(code)).toEqual([]);
});
