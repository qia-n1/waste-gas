<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  ArrowLeft,
  ArrowRight,
  Calendar,
  DArrowLeft,
  DArrowRight,
  Delete,
  Download,
  Edit,
  Hide,
  Key,
  Medal,
  Message,
  Operation,
  Plus,
  Search,
  Select,
  User,
  View,
} from "@element-plus/icons-vue";

import HeaderBar from "@/components/layout/HeaderBar.vue";
import { createUser, fetchUserDetail, fetchUsers, resetUserPassword, toggleUserStatus, updateUser } from "@/api/users";
import { useAuthStore } from "@/stores/auth";
import type { UserFormPayload, UserListItem, UserRoleOption } from "@/types/users";

const authStore = useAuthStore();
const router = useRouter();

const metrics = reactive({
  currentVocs: 0,
  peakForecast: 0,
  alertLevel: "normal",
  onlineDevices: 0,
  totalDevices: 0,
  todayAlerts: 0,
  systemPhase: "用户管理",
  uptime: "--",
  confidence: 0,
  dataCompleteness: 0,
  latencyMs: 0,
  predictionType: "manual",
});

const loading = ref(false);
const users = ref<UserListItem[]>([]);
const roles = ref<UserRoleOption[]>([]);
const selectedRows = ref<UserListItem[]>([]);
const detailVisible = ref(false);
const formVisible = ref(false);
const isEditing = ref(false);
const currentDetail = ref<{ item: UserListItem; permissions: { menus: string[] } } | null>(null);

const filters = reactive({
  keyword: "",
  roleCodes: [] as string[],
  status: "",
});

const pageSize = ref(12);
const currentPage = ref(1);

const userForm = reactive<Required<UserFormPayload>>({
  username: "",
  display_name: "",
  role_code: "EnvAdmin",
  status: "enabled",
  password: "",
});

const roleNameMap: Record<string, string> = {
  SysAdmin: "超级管理员",
  EnvAdmin: "环保监测员",
  Analyst: "数据分析师",
  Operator: "现场处置工",
};

const roleToneMap: Record<string, string> = {
  SysAdmin: "tone-cyan",
  EnvAdmin: "tone-lime",
  Analyst: "tone-blue",
  Operator: "tone-slate",
};

const statusLabel = (status: string) => (status === "enabled" ? "启用" : "禁用");
const statusClass = (status: string) => (status === "enabled" ? "status-enabled" : "status-disabled");
const roleLabel = (roleCode: string, roleName?: string) =>
  roleName || roles.value.find((item) => item.code === roleCode)?.name || roleNameMap[roleCode] || roleCode;

const filteredSummary = computed(() => {
  const enabledCount = users.value.filter((item) => item.status === "enabled").length;
  return {
    total: users.value.length,
    enabled: enabledCount,
    disabled: users.value.length - enabledCount,
  };
});

const totalPages = computed(() => Math.max(1, Math.ceil(users.value.length / pageSize.value)));

const pagedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return users.value.slice(start, start + pageSize.value);
});

const pageRangeLabel = computed(() => {
  if (users.value.length === 0) {
    return "0 条";
  }
  const start = (currentPage.value - 1) * pageSize.value + 1;
  const end = Math.min(currentPage.value * pageSize.value, users.value.length);
  return `${start}-${end} / 共 ${users.value.length} 条`;
});

const visiblePages = computed(() => {
  const total = totalPages.value;
  const current = currentPage.value;
  const pages: (number | "gap")[] = [];
  if (total <= 5) {
    for (let i = 1; i <= total; i += 1) pages.push(i);
    return pages;
  }
  pages.push(1);
  if (current > 3) pages.push("gap");
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);
  for (let i = start; i <= end; i += 1) pages.push(i);
  if (current < total - 2) pages.push("gap");
  pages.push(total);
  return pages;
});

const goToPage = (page: number) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
};

const resetForm = () => {
  userForm.username = "";
  userForm.display_name = "";
  userForm.role_code = "EnvAdmin";
  userForm.status = "enabled";
  userForm.password = "";
};

const loadUsers = async () => {
  loading.value = true;
  try {
    const data = await fetchUsers(filters);
    users.value = data.items;
    roles.value = data.roles;
    metrics.onlineDevices = data.items.filter((item) => item.status === "enabled").length;
    metrics.totalDevices = data.items.length;
    if (currentPage.value > totalPages.value) currentPage.value = 1;
  } finally {
    loading.value = false;
  }
};

const handleLogout = async () => {
  authStore.logout();
  await router.push("/login");
};

const handleSearch = async () => {
  currentPage.value = 1;
  await loadUsers();
};

const handleResetFilters = async () => {
  filters.keyword = "";
  filters.roleCodes = [];
  filters.status = "";
  currentPage.value = 1;
  await loadUsers();
};

const handleViewDetail = async (row: UserListItem) => {
  currentDetail.value = await fetchUserDetail(row.id);
  detailVisible.value = true;
};

const handleOpenCreate = () => {
  resetForm();
  isEditing.value = false;
  formVisible.value = true;
};

const handleOpenEdit = (row: UserListItem) => {
  resetForm();
  isEditing.value = true;
  userForm.username = row.username;
  userForm.display_name = row.display_name;
  userForm.role_code = row.role_code;
  userForm.status = row.status;
  formVisible.value = true;
  currentDetail.value = { item: row, permissions: { menus: [] } };
};

const handleSubmitForm = async () => {
  try {
    if (isEditing.value && currentDetail.value) {
      await updateUser(currentDetail.value.item.id, {
        display_name: userForm.display_name,
        role_code: userForm.role_code,
        status: userForm.status,
      });
      ElMessage.success("用户信息已更新");
    } else {
      await createUser({
        username: userForm.username,
        display_name: userForm.display_name,
        role_code: userForm.role_code,
        status: userForm.status,
        password: userForm.password,
      });
      ElMessage.success("已新增用户");
    }
    formVisible.value = false;
    resetForm();
    await loadUsers();
  } catch (error) {
    console.error(error);
    ElMessage.error("保存用户失败");
  }
};

const handleResetPassword = async (row: UserListItem) => {
  try {
    const result = await resetUserPassword(row.id);
    ElMessage.success(result.message);
  } catch (error) {
    console.error(error);
    ElMessage.error("重置密码失败");
  }
};

const handleToggleStatus = async (row: UserListItem) => {
  const actionLabel = row.status === "enabled" ? "禁用" : "启用";
  try {
    await ElMessageBox.confirm(
      `确认要${actionLabel}用户 ${row.display_name} 吗？`,
      `${actionLabel}用户`,
      {
        confirmButtonText: "确认",
        cancelButtonText: "取消",
        type: "warning",
      },
    );
    await toggleUserStatus(row.id);
    ElMessage.success(`已${actionLabel}用户`);
    await loadUsers();
  } catch (error) {
    if (error !== "cancel") {
      console.error(error);
      ElMessage.error(`${actionLabel}用户失败`);
    }
  }
};

const handleDownloadCsv = () => {
  if (users.value.length === 0) {
    ElMessage.info("暂无数据可导出");
    return;
  }
  const header = ["用户名", "姓名/展示名", "角色", "状态", "创建时间", "最后登录时间"];
  const rows = users.value.map((item) => [
    item.username,
    item.display_name,
    roleLabel(item.role_code, item.role_name),
    statusLabel(item.status),
    item.created_at,
    item.last_login_at,
  ]);
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell ?? "").replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([`\ufeff${csv}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `users_${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
};

onMounted(async () => {
  await loadUsers();
});
</script>

<template>
  <div class="user-page">
    <HeaderBar
      :metrics="metrics"
      :connected="true"
      :user-name="authStore.user?.name ?? '管理员'"
      @logout="handleLogout"
    />

    <main class="user-page__content">
      <section class="users-shell">
        <header class="users-head">
          <div class="users-head__left">
            <h2 class="users-head__title">用户列表</h2>
            <div class="summary-chips">
              <span class="summary-chip"><em>总数</em><strong>{{ filteredSummary.total }}</strong></span>
              <span class="summary-chip"><em>启用</em><strong class="dot-enabled">{{ filteredSummary.enabled }}</strong></span>
              <span class="summary-chip"><em>禁用</em><strong class="dot-disabled">{{ filteredSummary.disabled }}</strong></span>
            </div>
          </div>

          <div class="users-head__right">
            <div class="search-box">
              <el-icon><Search /></el-icon>
              <input
                v-model="filters.keyword"
                type="text"
                placeholder="搜索用户"
                @keyup.enter="handleSearch"
              />
            </div>
            <button class="ghost-btn" type="button" @click="handleResetFilters">
              <el-icon><Hide /></el-icon>
              重置筛选
            </button>
            <button class="ghost-btn" type="button" @click="handleDownloadCsv">
              <el-icon><Download /></el-icon>
              导出 CSV
            </button>
            <button class="primary-btn" type="button" @click="handleOpenCreate">
              <el-icon><Plus /></el-icon>
              新增用户
            </button>
          </div>
        </header>

        <div class="filter-row">
          <el-select
            v-model="filters.roleCodes"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="按角色筛选"
            class="filter-pill"
            @change="handleSearch"
          >
            <el-option
              v-for="role in roles"
              :key="role.code"
              :label="role.name"
              :value="role.code"
            />
          </el-select>
          <el-select
            v-model="filters.status"
            placeholder="按状态筛选"
            clearable
            class="filter-pill"
            @change="handleSearch"
          >
            <el-option label="启用" value="enabled" />
            <el-option label="禁用" value="disabled" />
          </el-select>
          <button class="add-filter" type="button" @click="handleSearch">
            <el-icon><Plus /></el-icon>
            应用筛选
          </button>
        </div>

        <div class="table-wrap" v-loading="loading">
          <table class="users-table">
            <thead>
              <tr>
                <th class="col-check"><span class="radio-mark" /></th>
                <th><span class="th-cell"><el-icon><User /></el-icon>用户名</span></th>
                <th><span class="th-cell"><el-icon><Message /></el-icon>姓名/展示名</span></th>
                <th><span class="th-cell"><el-icon><Medal /></el-icon>角色</span></th>
                <th><span class="th-cell"><el-icon><Select /></el-icon>状态</span></th>
                <th><span class="th-cell"><el-icon><Calendar /></el-icon>创建时间</span></th>
                <th><span class="th-cell"><el-icon><Key /></el-icon>最后登录时间</span></th>
                <th><span class="th-cell"><el-icon><Operation /></el-icon>操作</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in pagedUsers" :key="row.id">
                <td class="col-check"><span class="radio-mark" /></td>
                <td class="cell-primary">{{ row.username }}</td>
                <td class="cell-muted">{{ row.display_name }}</td>
                <td>
                  <span class="role-text" :class="roleToneMap[row.role_code]">
                    {{ roleLabel(row.role_code, row.role_name) }}
                  </span>
                </td>
                <td>
                  <span class="status-text" :class="statusClass(row.status)">
                    {{ statusLabel(row.status) }}
                  </span>
                </td>
                <td class="cell-muted">{{ row.created_at }}</td>
                <td class="cell-muted">{{ row.last_login_at || "—" }}</td>
                <td>
                  <div class="row-actions">
                    <button class="row-btn" type="button" @click="handleViewDetail(row)">
                      <el-icon><View /></el-icon>详情
                    </button>
                    <button class="row-btn" type="button" @click="handleOpenEdit(row)">
                      <el-icon><Edit /></el-icon>编辑
                    </button>
                    <button class="row-btn" type="button" @click="handleResetPassword(row)">
                      <el-icon><Key /></el-icon>重置密码
                    </button>
                    <button
                      class="row-btn"
                      :class="row.status === 'enabled' ? 'row-btn-warn' : 'row-btn-success'"
                      type="button"
                      @click="handleToggleStatus(row)"
                    >
                      <el-icon><Delete /></el-icon>
                      {{ row.status === "enabled" ? "禁用" : "启用" }}
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="!loading && pagedUsers.length === 0">
                <td colspan="8" class="empty-row">暂无用户数据</td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="pager">
          <div class="pager__left">
            <span>每页</span>
            <el-select v-model="pageSize" class="page-size-select" @change="currentPage = 1">
              <el-option :value="12" label="12" />
              <el-option :value="24" label="24" />
              <el-option :value="48" label="48" />
            </el-select>
            <span class="pager__range">{{ pageRangeLabel }}</span>
          </div>
          <div class="pager__right">
            <button class="pager-btn" :disabled="currentPage === 1" @click="goToPage(1)">
              <el-icon><DArrowLeft /></el-icon>
            </button>
            <button class="pager-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
              <el-icon><ArrowLeft /></el-icon>
            </button>
            <template v-for="(item, idx) in visiblePages" :key="`${item}-${idx}`">
              <span v-if="item === 'gap'" class="pager-gap">…</span>
              <button
                v-else
                class="pager-btn"
                :class="{ 'pager-btn-active': item === currentPage }"
                @click="goToPage(item)"
              >
                {{ item }}
              </button>
            </template>
            <button class="pager-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">
              <el-icon><ArrowRight /></el-icon>
            </button>
            <button class="pager-btn" :disabled="currentPage === totalPages" @click="goToPage(totalPages)">
              <el-icon><DArrowRight /></el-icon>
            </button>
          </div>
        </footer>
      </section>
    </main>

    <el-dialog
      v-model="formVisible"
      :title="isEditing ? '编辑用户' : '新增用户'"
      width="520px"
      class="user-dialog"
    >
      <el-form label-position="top">
        <el-form-item label="用户名" v-if="!isEditing">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名/展示名">
          <el-input v-model="userForm.display_name" placeholder="请输入展示名" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.role_code">
            <el-option v-for="role in roles" :key="role.code" :label="role.name" :value="role.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="userForm.status">
            <el-option label="启用" value="enabled" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item label="初始密码" v-if="!isEditing">
          <el-input v-model="userForm.password" type="password" show-password placeholder="请输入初始密码" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailVisible"
      title="用户详情"
      width="500px"
      class="user-dialog"
    >
      <template v-if="currentDetail">
        <div class="detail-grid">
          <div class="detail-item">
            <span>用户名</span>
            <strong>{{ currentDetail.item.username }}</strong>
          </div>
          <div class="detail-item">
            <span>姓名/展示名</span>
            <strong>{{ currentDetail.item.display_name }}</strong>
          </div>
          <div class="detail-item">
            <span>角色</span>
            <strong>{{ roleLabel(currentDetail.item.role_code, currentDetail.item.role_name) }}</strong>
          </div>
          <div class="detail-item">
            <span>状态</span>
            <strong>{{ statusLabel(currentDetail.item.status) }}</strong>
          </div>
          <div class="detail-item">
            <span>创建时间</span>
            <strong>{{ currentDetail.item.created_at }}</strong>
          </div>
          <div class="detail-item">
            <span>最后登录时间</span>
            <strong>{{ currentDetail.item.last_login_at }}</strong>
          </div>
        </div>
        <div class="permissions-panel">
          <p>菜单权限</p>
          <div class="permissions-list">
            <span v-for="menu in currentDetail.permissions.menus" :key="menu">{{ menu }}</span>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.user-page {
  width: 100%;
  height: 100%;
  padding: 18px;
  display: grid;
  grid-template-rows: 88px minmax(0, 1fr);
  gap: 14px;
}

.user-page__content {
  min-height: 0;
}

.users-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px 28px 20px;
  border-radius: var(--panel-radius);
  border: 1px solid var(--border-color);
  background:
    linear-gradient(180deg, rgba(23, 37, 69, 0.9), rgba(11, 19, 39, 0.88)),
    rgba(11, 19, 39, 0.88);
  box-shadow: var(--shadow-glow);
  backdrop-filter: blur(16px);
  overflow: hidden;
}

.users-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 18px;
}

.users-head__left {
  display: flex;
  align-items: center;
  gap: 18px;
}

.users-head__title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.01em;
}

.summary-chips {
  display: flex;
  gap: 8px;
}

.summary-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid var(--border-color);
  background: rgba(8, 16, 33, 0.6);
  color: var(--text-secondary);
  font-size: 12px;
}

.summary-chip em {
  font-style: normal;
  opacity: 0.95;
}

.summary-chip strong {
  color: var(--text-primary);
  font-weight: 600;
}

.dot-enabled {
  color: var(--accent-green) !important;
}

.dot-disabled {
  color: var(--accent-red) !important;
}

.users-head__right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.search-box {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  height: 36px;
  min-width: 240px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  background: rgba(8, 16, 33, 0.6);
  color: var(--text-secondary);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.search-box:focus-within {
  border-color: var(--border-strong);
  background: rgba(8, 16, 33, 0.82);
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
}

.search-box input::placeholder {
  color: var(--text-muted);
}

.ghost-btn,
.primary-btn,
.add-filter {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.ghost-btn {
  border: 1px solid var(--border-color);
  background: rgba(8, 16, 33, 0.6);
  color: var(--text-primary);
}

.ghost-btn:hover {
  border-color: var(--border-strong);
  background: rgba(83, 209, 255, 0.12);
  color: var(--accent-cyan);
}

.primary-btn {
  border: 1px solid rgba(83, 209, 255, 0.45);
  background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-blue) 100%);
  color: #07101d;
  font-weight: 600;
  box-shadow: 0 6px 20px rgba(83, 209, 255, 0.32);
}

.primary-btn:hover {
  filter: brightness(1.1);
  box-shadow: 0 8px 28px rgba(83, 209, 255, 0.45);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 14px;
}

.filter-pill {
  width: 180px;
}

.filter-pill :deep(.el-select__wrapper) {
  min-height: 36px;
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid var(--border-color) !important;
  background: rgba(8, 16, 33, 0.6) !important;
  box-shadow: none !important;
}

.filter-pill :deep(.el-select__wrapper.is-hovering:not(.is-focused)) {
  border-color: var(--border-strong) !important;
  box-shadow: none !important;
}

.filter-pill :deep(.el-select__wrapper.is-focused) {
  border-color: var(--accent-cyan) !important;
  box-shadow: none !important;
}

.filter-pill :deep(.el-select__placeholder) {
  color: var(--text-secondary);
  font-size: 13px;
}

.filter-pill :deep(.el-select__selected-item) {
  color: var(--text-primary);
}

.add-filter {
  border: 1px dashed var(--border-strong);
  background: rgba(8, 16, 33, 0.4);
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 0 14px;
}

.add-filter:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
  border-radius: 14px;
  border: 1px solid var(--border-color);
  background: rgba(8, 16, 33, 0.45);
}

.users-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 13px;
  color: var(--text-primary);
}

.users-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 14px 16px;
  text-align: left;
  font-weight: 500;
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(11, 19, 39, 0.96);
  border-bottom: 1px solid var(--border-color);
}

.th-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.th-cell .el-icon {
  font-size: 14px;
  color: var(--accent-cyan);
}

.users-table tbody td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(87, 140, 255, 0.1);
  white-space: nowrap;
  vertical-align: middle;
}

.users-table tbody tr:hover td {
  background: rgba(83, 209, 255, 0.06);
}

.col-check {
  width: 44px;
}

.radio-mark {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid var(--border-strong);
}

.cell-primary {
  color: var(--text-primary);
  font-weight: 500;
}

.cell-muted {
  color: var(--text-secondary);
}

.role-text {
  font-weight: 500;
}

.tone-cyan {
  color: var(--accent-cyan);
}

.tone-lime {
  color: var(--accent-green);
}

.tone-blue {
  color: var(--accent-blue);
}

.tone-slate {
  color: var(--text-secondary);
}

.status-text {
  font-weight: 500;
}

.status-enabled {
  color: var(--accent-green);
}

.status-disabled {
  color: var(--accent-red);
}

.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.row-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  padding: 0 10px;
  font-size: 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: rgba(8, 16, 33, 0.6);
  color: var(--text-primary);
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, color 0.2s ease;
}

.row-btn .el-icon {
  font-size: 12px;
}

.row-btn:hover {
  border-color: var(--accent-cyan);
  background: rgba(83, 209, 255, 0.12);
  color: var(--accent-cyan);
}

.row-btn-warn {
  color: var(--accent-amber);
}

.row-btn-warn:hover {
  border-color: rgba(255, 179, 71, 0.55);
  background: rgba(255, 179, 71, 0.12);
  color: var(--accent-amber);
}

.row-btn-success {
  color: var(--accent-green);
}

.row-btn-success:hover {
  border-color: rgba(64, 223, 154, 0.55);
  background: rgba(64, 223, 154, 0.12);
  color: var(--accent-green);
}

.empty-row {
  padding: 40px 16px !important;
  text-align: center;
  color: var(--text-muted);
}

.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16px;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 12px;
}

.pager__left {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.page-size-select {
  width: 80px;
}

.page-size-select :deep(.el-select__wrapper) {
  min-height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color) !important;
  background: rgba(8, 16, 33, 0.6) !important;
  box-shadow: none !important;
}

.page-size-select :deep(.el-select__selected-item) {
  color: var(--text-primary);
}

.pager__right {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.pager-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: rgba(8, 16, 33, 0.6);
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, color 0.2s ease;
}

.pager-btn:hover:not(:disabled) {
  border-color: var(--accent-cyan);
  background: rgba(83, 209, 255, 0.12);
  color: var(--accent-cyan);
}

.pager-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pager-btn-active {
  border-color: var(--accent-cyan);
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
  color: #07101d;
  font-weight: 600;
}

.pager-gap {
  padding: 0 4px;
  color: var(--text-muted);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-item {
  padding: 12px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: rgba(8, 16, 33, 0.45);
}

.detail-item span {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
}

.detail-item strong {
  display: block;
  margin-top: 6px;
  color: var(--text-primary);
}

.permissions-panel {
  margin-top: 16px;
  padding: 14px;
  border-radius: 12px;
  background: rgba(8, 16, 33, 0.45);
  border: 1px solid var(--border-color);
}

.permissions-panel p {
  margin: 0 0 10px;
  color: var(--text-secondary);
  font-weight: 500;
}

.permissions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.permissions-list span {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(83, 209, 255, 0.1);
  border: 1px solid rgba(83, 209, 255, 0.25);
  color: var(--accent-cyan);
  font-size: 12px;
}

@media (max-width: 1380px) {
  .users-head {
    flex-direction: column;
    align-items: stretch;
  }

  .users-head__right {
    justify-content: flex-end;
  }
}

@media (max-width: 980px) {
  .users-shell {
    padding: 18px;
  }

  .users-head__left {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-box {
    min-width: 0;
    flex: 1;
  }

  .filter-row {
    flex-wrap: wrap;
  }

  .filter-pill {
    width: 100%;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
