import Fastify from 'fastify';
import fastifyCookie from '@fastify/cookie';
import fastifySecureSession from '@fastify/secure-session';
import fastifyStatic from '@fastify/static';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

import './db.js';
import authRoutes from './routes/auth.js';
import dashboardRoutes from './routes/dashboard.js';
import timesheetRoutes from './routes/timesheet.js';
import entriesRoutes from './routes/entries.js';
import projectsRoutes from './routes/projects.js';
import usersRoutes from './routes/users.js';
import reportsRoutes from './routes/reports.js';
import exportRoutes from './routes/export.js';

const PORT = Number(process.env.PORT ?? 8000);
const HOST = process.env.HOST ?? '0.0.0.0';
const SESSION_SECRET = process.env.SESSION_SECRET;
if (!SESSION_SECRET) throw new Error('SESSION_SECRET env var required');
const WEB_DIST = process.env.WEB_DIST ?? resolve(dirname(fileURLToPath(import.meta.url)), '../../web/build');

const sessionKey = createHash('sha256').update(SESSION_SECRET).digest();

async function main() {
  const app = Fastify({ logger: true });

  await app.register(fastifyCookie);
  // path:'/' is essential — without it the cookie defaults to the login route's
  // directory (/api/auth) and never reaches /api/dashboard, /api/timesheet, etc.
  await app.register(fastifySecureSession, {
    key: sessionKey,
    cookie: { path: '/', httpOnly: true, sameSite: 'lax', secure: true },
  });

  await app.register(authRoutes, { prefix: '/api' });
  await app.register(dashboardRoutes, { prefix: '/api' });
  await app.register(timesheetRoutes, { prefix: '/api' });
  await app.register(entriesRoutes, { prefix: '/api' });
  await app.register(projectsRoutes, { prefix: '/api' });
  await app.register(usersRoutes, { prefix: '/api' });
  await app.register(reportsRoutes, { prefix: '/api' });
  await app.register(exportRoutes, { prefix: '/api' });

  if (existsSync(WEB_DIST)) {
    await app.register(fastifyStatic, { root: resolve(WEB_DIST), prefix: '/' });
    app.setNotFoundHandler((req: any, reply: any) => {
      if (req.url.startsWith('/api')) return reply.code(404).send({ error: 'Not found' });
      return reply.sendFile('index.html');
    });
  } else {
    app.setNotFoundHandler((req: any, reply: any) => {
      if (req.url.startsWith('/api')) return reply.code(404).send({ error: 'Not found' });
      return reply.code(404).send({ error: 'Web build not found' });
    });
  }

  try {
    await app.listen({ port: PORT, host: HOST });
    app.log.info(`Timesheet API listening on http://${HOST}:${PORT}`);
    app.log.info(`Serving web from ${WEB_DIST}`);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
}

main();