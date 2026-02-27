const path = require('path')
const baseDir = path.resolve(__dirname)

module.exports = {
  apps: [
    {
      name: 'sukuyodo-backend',
      cwd: path.join(baseDir, 'backend'),
      script: 'venv/bin/uvicorn',
      args: 'main:app --port 8001',
      interpreter: 'none',
      env: {
        PATH: path.join(baseDir, 'backend', 'venv', 'bin') + ':' + process.env.PATH
      }
    },
    {
      name: 'sukuyodo-frontend',
      cwd: path.join(baseDir, 'frontend'),
      script: 'npm',
      args: 'run dev -- --port 5171',
      interpreter: 'none'
    }
  ]
}
