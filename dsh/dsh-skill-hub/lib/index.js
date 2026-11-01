/**
 * dsh-skill-hub host plugin.
 *
 * Configures GitHub repositories, scans them for skills, installs or updates
 * those skills into `$DSH_HOME/skill-hub/skills`, and registers them with the
 * running harness so they are immediately available in every session.
 *
 * @module dsh-skill-hub
 */
import { API_PATH, createApiHandler } from './api.js';
import { SkillHubService } from './service.js';
import { dataPath } from './store.js';

/** Cordis plugin name. */
export const name = 'skill-hub';

/** Services this plugin needs: the skill registry and an HTTP mount point. */
export const inject = ['skills', 'webServer'];

/**
 * Mount the service and its HTTP endpoint.
 * @param ctx - the cordis plugin context.
 */
export function apply(ctx) {
  const logger = ctx.logger(name);
  const service = new SkillHubService(ctx.skills, logger);

  ctx.webServer.register({
    name: 'skill-hub-api',
    kind: 'exact',
    path: API_PATH,
    handler: createApiHandler(service, logger),
  });

  if (typeof ctx.effect === 'function') {
    ctx.effect(() => () => service.dispose());
  }

  logger.info(
    `skill-hub: 就绪，运行时注册 ${service.disposers.length} 个技能，数据目录 ${dataPath()}`,
  );
}

export { SkillHubService };
