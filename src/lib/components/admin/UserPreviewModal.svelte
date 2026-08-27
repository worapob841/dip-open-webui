<script lang="ts">
	import { getContext } from 'svelte';
	import dayjs from 'dayjs';
	import localizedFormat from 'dayjs/plugin/localizedFormat';
	dayjs.extend(localizedFormat);

	import { getUserPreview, getUserQuotaByUserId, type UserQuotaInfo } from '$lib/apis/users';
	import { config } from '$lib/stores';
	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n = getContext('i18n');

	export let show = false;
	export let userId: string = '';
	export let userName: string = '';

	let loading = true;
	let preview: any = null;
	let error: string = '';

	let quota: UserQuotaInfo | null = null;
	let quotaLoading = true;

	$: if (show && userId) {
		loadPreview();
		loadQuota();
	}

	const loadPreview = async () => {
		loading = true;
		error = '';
		try {
			preview = await getUserPreview(localStorage.token, userId);
		} catch (e) {
			error = String(e);
		} finally {
			loading = false;
		}
	};

	const loadQuota = async () => {
		if (!$config?.features?.enable_litellm_quota) {
			quotaLoading = false;
			return;
		}
		quotaLoading = true;
		try {
			quota = await getUserQuotaByUserId(localStorage.token, userId);
		} catch (e) {
			quota = null;
		} finally {
			quotaLoading = false;
		}
	};
</script>

<Modal size="md" bind:show>
	<div>
		<div class=" flex justify-between dark:text-gray-100 px-4 pt-3 mb-1">
			<div class=" text-sm font-medium self-center min-w-0 truncate">
				{$i18n.t('User Preview')}
				{#if userName}
					<span class="text-sm font-normal text-gray-500 ml-1">{userName}</span>
				{/if}
			</div>
			<button
				class="self-center flex-shrink-0"
				on:click={() => {
					show = false;
				}}
			>
				<XMark className={'size-4'} />
			</button>
		</div>

		<div class="flex flex-col w-full px-5 pb-4">
			{#if loading}
				<div class="flex justify-center items-center py-8">
					<Spinner className="size-5" />
				</div>
			{:else if error}
				<div class="text-red-500 text-xs text-center py-4">{error}</div>
			{:else if preview}
				<div class="space-y-2">
					{#if $config?.features?.enable_litellm_quota}
							<div>
								<div class=" mb-2 text-sm font-normal">{$i18n.t('Quota')}</div>
								{#if quotaLoading}
									<div class="flex w-full justify-between my-1">
										<Spinner className="size-3" />
									</div>
								{:else if !quota || !quota.available}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs text-gray-500">
											{$i18n.t('Quota information unavailable')}
										</div>
									</div>
								{:else if !quota.has_usage}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs text-gray-500">
											{$i18n.t('No usage yet')}
										</div>
									</div>
								{:else}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs font-normal">
											{#if quota.max_budget !== null}
												${quota.spend.toFixed(2)} / ${quota.max_budget.toFixed(2)}
											{:else}
												${quota.spend.toFixed(2)} - {$i18n.t('Unlimited')}
											{/if}
										</div>
									</div>
									{#if quota.budget_reset_at}
										<div class="flex w-full justify-between my-1">
											<div class=" self-center text-xs text-gray-500">
												{$i18n.t('Resets on')}
												{dayjs(quota.budget_reset_at).format('LL')}
											</div>
										</div>
									{/if}
								{/if}
							</div>

							<hr class="border-gray-50 dark:border-gray-850/30 my-1" />
						{/if}

						{#if preview.groups.length > 0}
						<div>
							<div class=" mb-2 text-sm font-normal">{$i18n.t('Groups')}</div>
							<div class="flex flex-col w-full">
								{#each preview.groups as group}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs font-normal">{group.name}</div>
									</div>
								{/each}
							</div>
						</div>

						<hr class="border-gray-50 dark:border-gray-850/30 my-1" />
					{/if}

					<div>
						<div class=" mb-2 text-sm font-normal">{$i18n.t('Models')}</div>
						<div class="flex flex-col w-full">
							{#if preview.models.items.length === 0}
								<div class="flex w-full justify-between my-1">
									<div class=" self-center text-xs text-gray-500">
										{$i18n.t('No models accessible')}
									</div>
								</div>
							{:else}
								{#each preview.models.items as model}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs font-normal">{model.name}</div>
									</div>
								{/each}

								{#if preview.models.total > preview.models.items.length}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs text-gray-500">
											{$i18n.t('{{count}} of {{total}} accessible', {
												count: preview.models.items.length,
												total: preview.models.total
											})}
										</div>
									</div>
								{/if}
							{/if}
						</div>
					</div>

					<hr class="border-gray-50 dark:border-gray-850/30 my-1" />

					<div>
						<div class=" mb-2 text-sm font-normal">{$i18n.t('Knowledge')}</div>
						<div class="flex flex-col w-full">
							{#if preview.knowledge.items.length === 0}
								<div class="flex w-full justify-between my-1">
									<div class=" self-center text-xs text-gray-500">
										{$i18n.t('No knowledge bases accessible')}
									</div>
								</div>
							{:else}
								{#each preview.knowledge.items as kb}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs font-normal">{kb.name}</div>
									</div>
								{/each}

								{#if preview.knowledge.total > preview.knowledge.items.length}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs text-gray-500">
											{$i18n.t('{{count}} of {{total}} accessible', {
												count: preview.knowledge.items.length,
												total: preview.knowledge.total
											})}
										</div>
									</div>
								{/if}
							{/if}
						</div>
					</div>

					<hr class="border-gray-50 dark:border-gray-850/30 my-1" />

					<div>
						<div class=" mb-2 text-sm font-normal">{$i18n.t('Tools')}</div>
						<div class="flex flex-col w-full">
							{#if preview.tools.items.length === 0}
								<div class="flex w-full justify-between my-1">
									<div class=" self-center text-xs text-gray-500">
										{$i18n.t('No tools accessible')}
									</div>
								</div>
							{:else}
								{#each preview.tools.items as tool}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs font-normal">{tool.name}</div>
									</div>
								{/each}

								{#if preview.tools.total > preview.tools.items.length}
									<div class="flex w-full justify-between my-1">
										<div class=" self-center text-xs text-gray-500">
											{$i18n.t('{{count}} of {{total}} accessible', {
												count: preview.tools.items.length,
												total: preview.tools.total
											})}
										</div>
									</div>
								{/if}
							{/if}
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
</Modal>
