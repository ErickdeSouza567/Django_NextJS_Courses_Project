type User = {
    id: number;
    name: string;
    email: string;
}

type SignInResponse = {
    user: User;
    access_toke: string
}

type SignUpResponse = {
    user: User;
    access_token: string
}