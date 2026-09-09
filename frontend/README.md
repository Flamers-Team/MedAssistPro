# Frontend

Aplicação React + Vite.

## Execução

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

## Build

```bash
npm run build
```

## Testes unitários

```bash
npm test          # roda uma vez (CI)
npm run test:watch  # modo watch
```

Usa Vitest + React Testing Library (`vite.config.js` tem a config de `test`, setup em `src/test/setup.js`).
