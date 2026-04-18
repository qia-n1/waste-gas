import client from "@/api/client";
import type {
  UserDetailResponse,
  UserFormPayload,
  UserListResponse,
} from "@/types/users";

export const fetchUsers = async (params?: {
  keyword?: string;
  roleCodes?: string[];
  status?: string;
}) => {
  const { data } = await client.get<UserListResponse>("/users", {
    params: {
      keyword: params?.keyword ?? "",
      role_codes: params?.roleCodes?.join(",") ?? "",
      status: params?.status ?? "",
    },
  });
  return data;
};

export const fetchUserDetail = async (userId: number) => {
  const { data } = await client.get<UserDetailResponse>(`/users/${userId}`);
  return data;
};

export const createUser = async (payload: UserFormPayload) => {
  const { data } = await client.post<{ item: UserDetailResponse["item"] }>("/users", payload);
  return data;
};

export const updateUser = async (userId: number, payload: UserFormPayload) => {
  const { data } = await client.put<{ item: UserDetailResponse["item"] }>(
    `/users/${userId}`,
    payload,
  );
  return data;
};

export const resetUserPassword = async (userId: number) => {
  const { data } = await client.post<{ success: boolean; message: string }>(
    `/users/${userId}/reset-password`,
  );
  return data;
};

export const toggleUserStatus = async (userId: number) => {
  const { data } = await client.post<{ item: UserDetailResponse["item"] }>(
    `/users/${userId}/toggle-status`,
  );
  return data;
};
