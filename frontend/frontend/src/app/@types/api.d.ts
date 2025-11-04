type API<Tdata> = {
    success: boolean;
    detail?: string | null;
    code?: string;
    data: TData | null;

}

type APIError = {
    success: false,
    detail?: string;
    code?: string
}