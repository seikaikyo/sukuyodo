module.exports = {
  apps: [
    {
      name: 'sukuyodo-backend',
      cwd: '/Users/dash/Documents/github/sukuyodo/backend',
      script: 'venv/bin/uvicorn',
      args: 'main:app --port 8001',
      interpreter: 'none',
      env: {
        PATH: '/Users/dash/Documents/github/sukuyodo/backend/venv/bin:' + process.env.PATH
      }
    },
    {
      name: 'sukuyodo-frontend',
      cwd: '/Users/dash/Documents/github/sukuyodo/frontend',
      script: 'npm',
      args: 'run dev -- --port 5174',
      interpreter: 'none'
    }
  ]
}
