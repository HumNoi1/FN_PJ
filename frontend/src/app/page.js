import { redirect } from "next/navigation";

export default function home() {
    redirect("/login");
}