export interface UserRoleOption {
  code: string;
  name: string;
}

export interface UserListItem {
  id: number;
  username: string;
  display_name: string;
  role_code: string;
  role_name: string;
  status: "enabled" | "disabled";
  created_at: string;
  last_login_at: string;
}

export interface UserListResponse {
  items: UserListItem[];
  total: number;
  roles: UserRoleOption[];
}

export interface UserDetailResponse {
  item: UserListItem;
  permissions: {
    menus: string[];
  };
}

export interface UserFormPayload {
  username?: string;
  display_name: string;
  role_code: string;
  status: "enabled" | "disabled";
  password?: string;
}
