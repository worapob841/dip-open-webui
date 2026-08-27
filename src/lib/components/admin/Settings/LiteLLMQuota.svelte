<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import {
		getLiteLLMQuotaConfig,
		setLiteLLMQuotaConfig,
		verifyLiteLLMQuotaConnection
	} from '$lib/apis/configs';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';

	const i18n = getContext('i18n');

	let loading = true;
	let saving = false;
	let verifying = false;
	let enabled = false;
	let baseUrl = '';
	let apiKey = '';
	let defaultBudgetId = '';

	onMount(async () => {
		try {
			const config = await getLiteLLMQuotaConfig(localStorage.token);
			enabled = config?.ENABLE_LITELLM_QUOTA ?? false;
			baseUrl = config?.LITELLM_ADMIN_BASE_URL ?? '';
			apiKey = config?.LITELLM_ADMIN_API_KEY ?? '';
			defaultBudgetId = config?.LITELLM_DEFAULT_BUDGET_ID ?? '';
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			loading = false;
		}
	});

	const verify = async () => {
		verifying = true;
		try {
			await verifyLiteLLMQuotaConnection(localStorage.token, {
				ENABLE_LITELLM_QUOTA: enabled,
				LITELLM_ADMIN_BASE_URL: baseUrl,
				LITELLM_ADMIN_API_KEY: apiKey,
				LITELLM_DEFAULT_BUDGET_ID: defaultBudgetId
			});
			toast.success($i18n.t('Connected to LiteLLM successfully.'));
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			verifying = false;
		}
	};

	const save = async () => {
		saving = true;
		try {
			await setLiteLLMQuotaConfig(localStorage.token, {
				ENABLE_LITELLM_QUOTA: enabled,
				LITELLM_ADMIN_BASE_URL: baseUrl,
				LITELLM_ADMIN_API_KEY: apiKey,
				LITELLM_DEFAULT_BUDGET_ID: defaultBudgetId
			});
			toast.success($i18n.t('Settings saved successfully!'));
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			saving = false;
		}
	};
</script>

<form class="flex h-full flex-col justify-between text-sm" on:submit|preventDefault={save}>
	<h2 class="text-sm font-medium text-gray-900 dark:text-white mb-4">{$i18n.t('LiteLLM Quota')}</h2>

	<div class="flex-1 min-h-0 overflow-y-auto scrollbar-hover pr-1.5">
		{#if loading}
			<div class="flex justify-center py-8"><Spinner className="size-6" /></div>
		{:else}
			<div class="flex flex-col gap-2.5">
				<label class="flex cursor-pointer items-center justify-between">
					<span class="text-xs text-gray-600 dark:text-gray-400">
						{$i18n.t('Show users their LiteLLM spend/budget')}
					</span>
					<Switch bind:state={enabled} />
				</label>
				<p class="-mt-1 text-[0.6875rem] text-gray-400 dark:text-gray-600">
					{$i18n.t(
						'Lets each user see their own LiteLLM spend, remaining budget, and reset time. Requires a LiteLLM key with the proxy_admin or proxy_admin_viewer role - your regular chat-completion key will not work.'
					)}
				</p>

				{#if enabled}
					<div>
						<label class="text-xs text-gray-600 dark:text-gray-400" for="llq-base-url">
							{$i18n.t('LiteLLM base URL')}
						</label>
						<input
							id="llq-base-url"
							type="text"
							bind:value={baseUrl}
							placeholder="http://litellm-service.nextgenai-llm.svc.cluster.local:4000"
							class="mt-1 h-7 w-full rounded-lg border border-gray-100/50 bg-gray-50/40 px-2 text-xs text-gray-700 outline-hidden transition-colors focus:border-blue-400 dark:border-white/[0.04] dark:bg-white/[0.03] dark:text-gray-300 dark:focus:border-blue-500"
						/>
					</div>

					<div>
						<label class="text-xs text-gray-600 dark:text-gray-400" for="llq-api-key">
							{$i18n.t('LiteLLM admin API key')}
						</label>
						<div class="mt-1">
							<SensitiveInput
								id="llq-api-key"
								type="password"
								bind:value={apiKey}
								placeholder="sk-..."
								required={false}
								variant="settings"
							/>
						</div>
						<p class="mt-0.5 text-[0.6875rem] text-gray-400 dark:text-gray-600">
							{$i18n.t(
								'Used server-side only, never sent to the browser. Create it with POST /key/generate and {"user_role": "proxy_admin_viewer"} against your LiteLLM master key.'
							)}
						</p>
					</div>

					<div>
						<label class="text-xs text-gray-600 dark:text-gray-400" for="llq-default-budget-id">
							{$i18n.t('Default budget ID (optional)')}
						</label>
						<input
							id="llq-default-budget-id"
							type="text"
							bind:value={defaultBudgetId}
							placeholder="hackathon-test-1k-2m"
							class="mt-1 h-7 w-full rounded-lg border border-gray-100/50 bg-gray-50/40 px-2 text-xs text-gray-700 outline-hidden transition-colors focus:border-blue-400 dark:border-white/[0.04] dark:bg-white/[0.03] dark:text-gray-300 dark:focus:border-blue-500"
						/>
						<p class="mt-0.5 text-[0.6875rem] text-gray-400 dark:text-gray-600">
							{$i18n.t(
								"Match your LiteLLM litellm_settings.max_end_user_budget_id. LiteLLM enforces this default budget for new users but doesn't persist it to their record, so without this set they'll show as Unlimited even though a limit is actually being enforced."
							)}
						</p>
					</div>

					<div>
						<button
							type="button"
							class="rounded-full border border-gray-100/50 bg-gray-50/40 px-3 py-1 text-xs text-gray-700 transition hover:bg-gray-100 disabled:opacity-50 dark:border-white/[0.04] dark:bg-white/[0.03] dark:text-gray-300 dark:hover:bg-white/[0.06]"
							disabled={verifying || !baseUrl || !apiKey}
							on:click={verify}
						>
							{verifying ? $i18n.t('Testing...') : $i18n.t('Test Connection')}
						</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>

	{#if !loading}
		<div class="flex justify-end pt-6 text-sm font-normal">
			<button
				class="rounded-full bg-black px-3.5 py-1.5 text-sm font-normal text-white transition hover:bg-gray-900 disabled:opacity-50 dark:bg-white dark:text-black dark:hover:bg-gray-100"
				type="submit"
				disabled={saving}
			>
				{$i18n.t('Save')}
			</button>
		</div>
	{/if}
</form>
