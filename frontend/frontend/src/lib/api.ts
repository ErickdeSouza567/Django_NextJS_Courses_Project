"use server";

import axios, { AxiosError } from "axios";

type Props = {
    endpoint: string;
    method?: "GET" | "POST" | "PUT" | "DELETE";
    data?: object;
    withAuth?: boolean;
};

const BASE_URL = process.env.API_URL + "/api/v1";

export const api = async <TypeResponse>({
    endpoint,
    method = "GET",
    data,
    withAuth = true
}: Props): Promise<API<TypeResponse>> => {

    const instance = axios.create({
        baseURL: BASE_URL
    });

    try {
        const response = await instance.request<API<TypeResponse>>({
            url: endpoint,
            method,
            params: method === "GET" ? data : undefined,
            data: method !== "GET" ? data : undefined,
            headers: withAuth ? {
                Authorization: `Bearer ${process.env.ACCESS_TOKEN}`
            } : undefined
        });

        return response.data;
    } catch (error) {
        const e = error as AxiosError<APIError>;

        return {
            success: false,
            detail: e.response?.data?.detail || "An unexpected error occurred",
            code: e.response?.data?.code || "UNKNOWN_ERROR",
            data: null
        };
    }
};
