<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Search } from "@element-plus/icons-vue";

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

const userForm = reactive<Required<UserFormPayload>>({
  username: "",
  display_name: "",
  role_code: "EnvAdmin",
  status: "enabled",
  password: "",
});

const roleTagClassMap: Record<string, string> = {
  SysAdmin: "role-sysadmin",
  EnvAdmin: "role-envadmin",
  Analyst: "role-analyst",
  Operator: "role-operator",
};

const roleNameMap: Record<string, string> = {
  SysAdmin: "超级管理员",
  EnvAdmin: "环保监测员",
  Analyst: "数据分析师",
  Operator: "现场处置工",
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
  } finally {
    loading.value = false;
  }
};

const handleLogout = async () => {
  authStore.logout();
  await router.push("/login");
};

const handleSearch = async () => {
  await loadUsers();
};

const handleResetFilters = async () => {
  filters.keyword = "";
  filters.roleCodes = [];
  filters.status = "";
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
      <section class="panel-card user-panel">
        <div class="page-head">
          <div>
            <p class="page-breadcrumb">用户管理 &gt; 用户列表</p>
            <h2>用户列表</h2>
          </div>
          <div class="page-stats">
            <div class="stats-chip">
              <span>总用户</span>
              <strong>{{ filteredSummary.total }}</strong>
            </div>
            <div class="stats-chip">
              <span>启用</span>
              <strong>{{ filteredSummary.enabled }}</strong>
            </div>
            <div class="stats-chip">
              <span>禁用</span>
              <strong>{{ filteredSummary.disabled }}</strong>
            </div>
          </div>
        </div>

        <div class="toolbar-card">
          <div class="filters-grid">
            <el-input
              v-model="filters.keyword"
              class="toolbar-search"
              placeholder="搜索用户名 / 姓名 / 角色"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>

            <div class="filter-group">
              <label>角色</label>
              <el-select
                v-model="filters.roleCodes"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="选择角色"
              >
                <el-option
                  v-for="role in roles"
                  :key="role.code"
                  :label="role.name"
                  :value="role.code"
                />
              </el-select>
            </div>

            <div class="filter-group">
              <label>状态</label>
              <el-select v-model="filters.status" placeholder="全部状态" clearable>
                <el-option label="启用" value="enabled" />
                <el-option label="禁用" value="disabled" />
              </el-select>
            </div>

            <div class="toolbar-actions">
              <el-button @click="handleResetFilters">重置</el-button>
              <el-button type="primary" @click="handleSearch">筛选</el-button>
              <el-button class="add-button" type="primary" @click="handleOpenCreate">
                <el-icon><Plus /></el-icon>
                新增用户
              </el-button>
            </div>
          </div>
        </div>

        <div class="table-shell">
          <el-table
            v-loading="loading"
            :data="users"
            class="users-table"
            @selection-change="selectedRows = $event"
          >
            <el-table-column type="selection" width="48" />
            <el-table-column prop="username" label="用户名" min-width="160" />
            <el-table-column prop="display_name" label="姓名/展示名" min-width="150" />
            <el-table-column label="角色" min-width="130">
              <template #default="{ row }">
                <span class="role-tag" :class="roleTagClassMap[row.role_code]">
                  {{ roleLabel(row.role_code, row.role_name) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="状态" min-width="90">
              <template #default="{ row }">
                <span class="status-pill" :class="statusClass(row.status)">
                  {{ statusLabel(row.status) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" min-width="160" />
            <el-table-column prop="last_login_at" label="最后登录时间" min-width="160" />
            <el-table-column label="操作" min-width="250" fixed="right">
              <template #default="{ row }">
                <div class="row-actions">
                  <button class="table-action action-link" @click="handleViewDetail(row)">详情</button>
                  <button class="table-action action-link" @click="handleOpenEdit(row)">编辑</button>
                  <button class="table-action action-link" @click="handleResetPassword(row)">重置密码</button>
                  <button
                    class="table-action"
                    :class="row.status === 'enabled' ? 'action-warn' : 'action-success'"
                    @click="handleToggleStatus(row)"
                  >
                    {{ row.status === "enabled" ? "禁用" : "启用" }}
                  </button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
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

.user-panel {
  padding: 18px 20px 20px;
  overflow: hidden;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-breadcrumb {
  margin: 0 0 6px;
  color: #72d5ff;
  font-size: 14px;
  letter-spacing: 0.04em;
}

.page-head h2 {
  margin: 0;
  font-size: 26px;
}

.page-stats {
  display: flex;
  gap: 10px;
}

.stats-chip {
  min-width: 92px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(89, 140, 233, 0.16);
  background: rgba(9, 18, 36, 0.46);
}

.stats-chip span {
  display: block;
  color: var(--text-secondary);
  font-size: 11px;
}

.stats-chip strong {
  display: block;
  margin-top: 8px;
  font-size: 20px;
}

.toolbar-card {
  margin-bottom: 14px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(100, 150, 244, 0.18);
  background: rgba(8, 16, 33, 0.5);
}

.filters-grid {
  display: grid;
  grid-template-columns: minmax(200px, 260px) minmax(220px, 1fr) 160px auto;
  gap: 14px;
  align-items: end;
}

.toolbar-search {
  width: 100%;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  color: #dce8ff;
  font-size: 13px;
  font-weight: 600;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.add-button {
  min-width: 132px;
  background: linear-gradient(135deg, #24dcff, #1ca6ff);
  border: none;
  color: #04111f;
  font-weight: 700;
}

.table-shell {
  height: calc(100% - 148px);
  min-height: 420px;
  padding: 4px;
  border-radius: 18px;
  border: 1px solid rgba(100, 150, 244, 0.16);
  background: rgba(8, 16, 33, 0.38);
}

.users-table {
  height: 100%;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 16, 33, 0.2);
  --el-table-header-bg-color: rgba(89, 104, 122, 0.42);
  --el-table-border-color: rgba(87, 217, 255, 0.28);
  --el-table-text-color: #f1f7ff;
  --el-table-header-text-color: #dce8ff;
  --el-table-row-hover-bg-color: rgba(33, 82, 153, 0.25);
}

:deep(.users-table .el-table__header-wrapper th),
:deep(.users-table .el-table__body-wrapper td) {
  border-right: 1px solid rgba(87, 217, 255, 0.26);
}

:deep(.users-table .el-table__inner-wrapper::before) {
  background-color: rgba(87, 217, 255, 0.26);
}

.role-tag,
.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 76px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.role-sysadmin {
  color: #55e0ff;
}

.role-envadmin {
  color: #c8ef63;
}

.role-analyst {
  color: #4a8bff;
}

.role-operator {
  color: #8d9cbc;
}

.status-enabled {
  background: rgba(46, 206, 113, 0.16);
  border: 1px solid rgba(46, 206, 113, 0.34);
  color: #58f296;
}

.status-disabled {
  background: rgba(255, 187, 64, 0.14);
  border: 1px solid rgba(255, 187, 64, 0.32);
  color: #ffd25f;
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.table-action {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.18s ease;
}

.table-action:hover {
  opacity: 0.8;
}

.action-link {
  color: #4ce0ff;
}

.action-warn {
  color: #ffd661;
}

.action-success {
  color: #6ef2a7;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-item {
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(95, 122, 191, 0.16);
  background: rgba(8, 16, 33, 0.5);
}

.detail-item span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.detail-item strong {
  display: block;
  margin-top: 8px;
}

.permissions-panel {
  margin-top: 16px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(8, 16, 33, 0.5);
}

.permissions-panel p {
  margin: 0 0 10px;
  color: #dce8ff;
  font-weight: 600;
}

.permissions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.permissions-list span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(56, 113, 222, 0.2);
  color: #beddff;
  font-size: 12px;
}

@media (max-width: 1380px) {
  .filters-grid {
    grid-template-columns: 1fr 1fr;
  }

  .toolbar-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}

@media (max-width: 980px) {
  .page-head {
    flex-direction: column;
  }

  .page-stats {
    width: 100%;
    flex-wrap: wrap;
  }

  .filters-grid {
    grid-template-columns: 1fr;
  }

  .table-shell {
    height: auto;
    min-height: 0;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
