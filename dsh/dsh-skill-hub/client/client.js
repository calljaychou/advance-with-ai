/**
 * dsh-skill-hub browser bundle.
 *
 * Hand-written lazy-CJS wrapper (the shared client build preset is not
 * published), contributing one settings section that talks to the host over
 * `/skill-hub/api`.
 */
window.__ModuleLoader__.load({
  id: 'dsh-skill-hub',
  factory: (require) => {
    const React = require('react');
    const h = React.createElement;
    const { useCallback, useEffect, useState } = React;

    /** Host endpoint backing this panel. */
    const API = '/skill-hub/api';

    /**
     * Call one host action.
     * @param action - the action name.
     * @param payload - the JSON payload.
     * @returns the action's value, or throws with the host message.
     */
    async function call(action, payload) {
      const response = await fetch(API, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ action, ...payload }),
      });
      const body = await response.json().catch(() => undefined);
      if (body === undefined) throw new Error(`接口无响应 (HTTP ${response.status})`);
      if (body.ok !== true) throw new Error(body.error?.message ?? `HTTP ${response.status}`);
      return body.value;
    }

    /** Border colour shared by every framed element. */
    const BORDER = '1px solid rgba(140,140,140,0.35)';
    /** Muted text colour. */
    const MUTED = { opacity: 0.65 };

    const styles = {
      wrap: { display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '13px', lineHeight: 1.6 },
      row: { display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' },
      input: {
        flex: '1 1 220px',
        minWidth: '180px',
        padding: '6px 9px',
        borderRadius: '6px',
        border: BORDER,
        background: 'transparent',
        color: 'inherit',
        fontSize: '13px',
      },
      button: {
        padding: '5px 11px',
        borderRadius: '6px',
        border: BORDER,
        background: 'transparent',
        color: 'inherit',
        fontSize: '12px',
        cursor: 'pointer',
      },
      primary: { border: '1px solid rgba(37,99,235,0.65)', color: '#2563eb', fontWeight: 600 },
      danger: { border: '1px solid rgba(220,38,38,0.55)', color: '#dc2626' },
      card: { border: BORDER, borderRadius: '8px', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '8px' },
      skill: { display: 'flex', gap: '10px', alignItems: 'flex-start', padding: '6px 0', borderTop: '1px solid rgba(140,140,140,0.2)' },
      mono: { fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: '11px', ...MUTED },
      note: { fontSize: '12px', ...MUTED },
    };

    /** Colour + label for one skill status. */
    const STATUS = {
      new: { label: '未安装', color: '#2563eb' },
      stale: { label: '可更新', color: '#d97706' },
      current: { label: '已最新', color: '#16a34a' },
      removed: { label: '仓库中已移除', color: '#dc2626' },
    };

    /**
     * Skill lists longer than this start folded, so a large repository cannot
     * stretch the settings panel into an endless scroll on first render.
     */
    const FOLD_THRESHOLD = 5;

    /**
     * A small coloured status chip.
     * @param props - `status` selects label and colour.
     * @returns the chip element.
     */
    function Chip(props) {
      const meta = STATUS[props.status] ?? { label: props.status, color: 'inherit' };
      return h(
        'span',
        { style: { color: meta.color, border: `1px solid ${meta.color}`, borderRadius: '10px', padding: '0 7px', fontSize: '11px', whiteSpace: 'nowrap' } },
        meta.label,
      );
    }

    /**
     * Format an ISO timestamp for display.
     * @param value - ISO timestamp.
     * @returns a short local time string.
     */
    function shortTime(value) {
      if (typeof value !== 'string' || value === '') return '未扫描';
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString();
    }

    /**
     * The settings section component.
     * @returns the panel element.
     */
    function SkillHubPanel() {
      const [state, setState] = useState(undefined);
      const [busy, setBusy] = useState('');
      const [error, setError] = useState('');
      const [repoInput, setRepoInput] = useState('');
      const [refInput, setRefInput] = useState('');
      /** Explicit per-repository fold overrides; absent ids fall back to the length default. */
      const [foldOverrides, setFoldOverrides] = useState({});

      /**
       * Run one host action, refreshing the rendered state.
       * @param key - the busy key shown while the action runs.
       * @param action - the host action name.
       * @param payload - the action payload.
       */
      const run = useCallback(async (key, action, payload) => {
        setBusy(key);
        setError('');
        try {
          const value = await call(action, payload);
          if (value?.state !== undefined) setState(value.state);
        } catch (failure) {
          setError(failure?.message ?? String(failure));
        } finally {
          setBusy('');
        }
      }, []);

      useEffect(() => {
        run('load', 'getState', {});
      }, [run]);

      if (state === undefined) {
        return h('div', { style: styles.wrap }, error === '' ? '正在加载技能仓库配置…' : h('div', { style: { color: '#dc2626' } }, error));
      }

      const repos = Array.isArray(state.repos) ? state.repos : [];
      const lastResult = state.lastResult;
      const catalog = Array.isArray(state.catalog) ? state.catalog : [];
      const ours = catalog.filter((skill) => String(skill.source ?? '').startsWith('skill-hub:'));

      /**
       * Whether a repository has work for the one-click button.
       * @param repo - one repository row.
       * @returns true when something can be installed or updated.
       */
      const hasWork = (repo) => (repo.counts?.new ?? 0) + (repo.counts?.stale ?? 0) > 0;

      /**
       * Whether one repository's skill list is currently folded.
       * @param repo - one repository row.
       * @returns true when the list collapses to a one-line summary.
       */
      const isFolded = (repo) => {
        const override = foldOverrides[repo.id];
        if (typeof override === 'boolean') return override;
        return (repo.skills?.length ?? 0) > FOLD_THRESHOLD;
      };

      /**
       * Fold or unfold one repository's skill list.
       * @param repo - one repository row.
       * @param value - the explicit fold state to remember.
       */
      const foldRepo = (repo, value) => setFoldOverrides((previous) => ({ ...previous, [repo.id]: value }));

      /**
       * Fold or unfold every configured repository at once.
       * @param value - the fold state applied to every repository.
       */
      const foldAll = (value) =>
        setFoldOverrides(() => {
          const next = {};
          for (const repo of repos) next[repo.id] = value;
          return next;
        });

      /**
       * Short one-line preview of a folded skill list.
       * @param repo - one repository row.
       * @returns the first few skill names, with a remainder count when longer.
       */
      const foldedPreview = (repo) => {
        const names = (repo.skills ?? []).map((skill) => skill.name);
        const head = names.slice(0, 3).join('、');
        return names.length > 3 ? `${head} 等 ${names.length} 个` : head;
      };

      /**
       * Render one skill row with its status chip and per-skill actions.
       * @param repo - the owning repository row.
       * @param skill - one scanned skill entry.
       * @returns the skill row element.
       */
      const skillRow = (repo, skill) => {
        const actionKey = `skill:${repo.id}:${skill.name}`;
        const verb = skill.status === 'new' ? '安装' : skill.status === 'stale' ? '更新' : skill.status === 'current' ? '重装' : '';
        return h(
          'div',
          { key: `${repo.id}:${skill.name}`, style: styles.skill },
          h(
            'div',
            { style: { flex: 1, minWidth: 0 } },
            h(
              'div',
              { style: styles.row },
              h('strong', null, skill.name),
              h(Chip, { status: skill.status }),
              skill.installedSha
                ? h('span', { style: styles.mono }, `已装 @${String(skill.installedSha).slice(0, 7)}`)
                : null,
            ),
            h('div', { style: styles.note }, skill.description || '(无描述)'),
          ),
          h(
            'div',
            { style: styles.row },
            verb === ''
              ? null
              : h(
                  'button',
                  {
                    style: {
                      ...styles.button,
                      ...(skill.status === 'new' || skill.status === 'stale' ? styles.primary : {}),
                    },
                    disabled: busy !== '',
                    title: `仅对 ${skill.name} 执行${verb}，来源 ${repo.repo}@${String(repo.sha ?? '').slice(0, 7)}`,
                    onClick: () => run(actionKey, 'installSkill', { id: repo.id, name: skill.name }),
                  },
                  busy === actionKey ? '处理中…' : verb,
                ),
            skill.status !== 'new'
              ? h(
                  'button',
                  { style: { ...styles.button, ...styles.danger }, disabled: busy !== '', onClick: () => run(`uninstall:${repo.id}:${skill.name}`, 'uninstall', { id: repo.id, name: skill.name }) },
                  '卸载',
                )
              : null,
          ),
        );
      };

      return h(
        'div',
        { style: styles.wrap },

        h(
          'div',
          null,
          h('div', { style: { fontWeight: 600 } }, '技能仓库（GitHub）'),
          h(
            'div',
            { style: styles.note },
            '配置一个或多个公开 GitHub 仓库，扫描其中的 SKILL.md，一键安装或更新到本机并立即注册给 Harness。',
          ),
          h(
            'div',
            { style: styles.note },
            '扫描完成后，每个技能都可单独「安装 / 更新 / 重装」，互不影响；也可以按仓库一键处理全部。',
          ),
          h(
            'div',
            { style: styles.note },
            `技能超过 ${FOLD_THRESHOLD} 个的仓库默认折叠，可单独「展开技能」或用「全部展开 / 全部折叠」。`,
          ),
          h('div', { style: styles.mono }, `数据目录：${state.dataDir}　运行时注册：${state.registered} 个技能`),
          h(
            'div',
            { style: styles.mono },
            `Harness 技能注册表：共 ${catalog.length} 个，其中本插件注册 ${ours.length} 个` +
              (ours.length > 0 ? `（${ours.map((skill) => skill.name).join('、')}）` : ''),
          ),
        ),

        h(
          'div',
          { style: styles.row },
          h('input', {
            style: styles.input,
            placeholder: 'owner/repo，或 https://github.com/owner/repo',
            value: repoInput,
            disabled: busy !== '',
            onChange: (event) => setRepoInput(event.target.value),
            onKeyDown: (event) => {
              if (event.key === 'Enter' && repoInput.trim() !== '') {
                run('add', 'addRepo', { repo: repoInput.trim(), ref: refInput.trim() });
                setRepoInput('');
              }
            },
          }),
          h('input', {
            style: { ...styles.input, flex: '0 1 150px', minWidth: '120px' },
            placeholder: '分支 / Tag（可选）',
            value: refInput,
            disabled: busy !== '',
            onChange: (event) => setRefInput(event.target.value),
          }),
          h(
            'button',
            {
              style: { ...styles.button, ...styles.primary },
              disabled: busy !== '' || repoInput.trim() === '',
              onClick: () => {
                run('add', 'addRepo', { repo: repoInput.trim(), ref: refInput.trim() });
                setRepoInput('');
              },
            },
            busy === 'add' ? '添加中…' : '添加并扫描',
          ),
        ),

        h(
          'div',
          { style: styles.row },
          h(
            'button',
            { style: styles.button, disabled: busy !== '' || repos.length === 0, onClick: () => run('scanAll', 'scanAll', {}) },
            busy === 'scanAll' ? '扫描中…' : '扫描全部',
          ),
          h(
            'button',
            { style: { ...styles.button, ...styles.primary }, disabled: busy !== '' || repos.length === 0, onClick: () => run('installAll', 'installAll', {}) },
            busy === 'installAll' ? '安装/更新中…' : '一键安装 / 更新全部',
          ),
          h('button', { style: styles.button, disabled: busy !== '', onClick: () => run('reload', 'reload', {}) }, '重新注册'),
          h(
            'button',
            { style: styles.button, disabled: busy !== '' || repos.length === 0, onClick: () => foldAll(true) },
            '全部折叠',
          ),
          h(
            'button',
            { style: styles.button, disabled: busy !== '' || repos.length === 0, onClick: () => foldAll(false) },
            '全部展开',
          ),
        ),

        error !== '' ? h('div', { style: { color: '#dc2626' } }, `错误：${error}`) : null,
        error === '' && lastResult?.message ? h('div', { style: { color: lastResult.ok ? '#16a34a' : '#d97706' } }, lastResult.message) : null,

        repos.length === 0
          ? h('div', { style: styles.note }, '还没有配置仓库。填入 owner/repo 后点「添加并扫描」，例如 liustack/modlens。')
          : null,

        ...repos.map((repo) =>
          h(
            'div',
            { key: repo.id, style: styles.card },
            h(
              'div',
              { style: styles.row },
              h('div', { style: { fontWeight: 600 } }, repo.label || repo.repo),
              repo.ref ? h('span', { style: styles.mono }, `ref: ${repo.ref}`) : null,
              repo.sha ? h('span', { style: styles.mono }, `@${String(repo.sha).slice(0, 7)}`) : null,
              h('span', { style: styles.note }, `已安装 ${repo.counts.installed}`),
              repo.counts.new > 0 ? h('span', { style: { color: '#2563eb' } }, `新 ${repo.counts.new}`) : null,
              repo.counts.stale > 0 ? h('span', { style: { color: '#d97706' } }, `可更新 ${repo.counts.stale}`) : null,
              h('span', { style: { flex: 1 } }),
              h(
                'button',
                {
                  style: styles.button,
                  disabled: (repo.skills?.length ?? 0) === 0,
                  onClick: () => foldRepo(repo, !isFolded(repo)),
                },
                `${isFolded(repo) ? '展开' : '折叠'}技能（${repo.skills?.length ?? 0}）`,
              ),
              h('button', { style: styles.button, disabled: busy !== '', onClick: () => run(`scan:${repo.id}`, 'scan', { id: repo.id }) }, busy === `scan:${repo.id}` ? '扫描中…' : '扫描'),
              h(
                'button',
                {
                  style: { ...styles.button, ...(hasWork(repo) ? styles.primary : {}) },
                  disabled: busy !== '' || (repo.skills?.length ?? 0) === 0,
                  onClick: () => run(`install:${repo.id}`, 'install', { id: repo.id, rescan: false }),
                },
                busy === `install:${repo.id}` ? '处理中…' : hasWork(repo) ? '一键安装 / 更新' : '校验并安装',
              ),
              h('button', { style: { ...styles.button, ...styles.danger }, disabled: busy !== '', onClick: () => run(`remove:${repo.id}`, 'removeRepo', { id: repo.id, uninstall: true }) }, '移除'),
            ),
            h(
              'div',
              { style: styles.note },
              `${shortTime(repo.scannedAt)}　${repo.skills?.length ?? 0} 个技能${repo.skipped?.length ? `　跳过 ${repo.skipped.length}` : ''}${isFolded(repo) ? '　已折叠' : ''}`,
            ),
            ...(isFolded(repo)
              ? [
                  h(
                    'div',
                    { key: `${repo.id}:folded`, style: styles.note },
                    `技能列表已折叠：${foldedPreview(repo)}　点「展开技能（${repo.skills?.length ?? 0}）」查看全部。`,
                  ),
                ]
              : (repo.skills ?? []).map((skill) => skillRow(repo, skill))),
            repo.skipped?.length
              ? h(
                  'details',
                  null,
                  h('summary', { style: styles.note }, `跳过的条目（${repo.skipped.length}）`),
                  ...repo.skipped.map((item, index) => h('div', { key: index, style: styles.mono }, `${item.path} — ${item.reason}`)),
                )
              : null,
          ),
        ),

        state.registrationFailures?.length
          ? h(
              'div',
              { style: { ...styles.card, borderColor: 'rgba(217,119,6,0.6)' } },
              h('div', { style: { fontWeight: 600, color: '#d97706' } }, `未注册的技能（${state.registrationFailures.length}）`),
              ...state.registrationFailures.map((item, index) => h('div', { key: index, style: styles.mono }, `${item.name} — ${item.reason}`)),
            )
          : null,
      );
    }

    /**
     * Register the settings section.
     * @param ctx - the client plugin context.
     */
    function apply(ctx) {
      ctx.slots.inject('settings.section', () =>
        ctx.slots.register(
          {
            name: 'settings.section',
            id: 'dsh-skill-hub',
            order: 20,
            label: () => '技能仓库',
            inject: () => ({}),
          },
          SkillHubPanel,
        ),
      );
    }

    return { name: 'dsh-skill-hub', inject: ['slots'], apply };
  },
});
