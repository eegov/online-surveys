// Правила сообщений коммитов: Conventional Commits (https://www.conventionalcommits.org/ru/v1.0.0/).
// Формат: <тип>(<область>): <описание>
// Пример: feat(server): добавить проверку состояния базы данных
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'revert'],
    ],
    'scope-enum': [2, 'always', ['server', 'client', 'db', 'ci', 'deps', 'docs', 'release']],
    'header-max-length': [2, 'always', 100],
    // Описание с маленькой буквы и без точки в конце, как в остальных правилах Conventional Commits.
    'subject-case': [2, 'never', ['sentence-case', 'start-case', 'pascal-case', 'upper-case']],
  },
};
