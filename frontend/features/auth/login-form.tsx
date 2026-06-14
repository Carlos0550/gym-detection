"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Mail } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { getMe, login } from "@/lib/api/auth";
import type { ApiError } from "@/lib/types/api";

const loginSchema = z.object({
  email: z.email("Email inválido"),
  password: z.string().min(8, "Mínimo 8 caracteres"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

type Props = {
  sessionExpired?: boolean;
};

export function LoginForm({ sessionExpired = false }: Props) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const mutation = useMutation({
    mutationFn: (values: LoginFormValues) => login(values.email, values.password),
    onSuccess: async () => {
      await queryClient.fetchQuery({ queryKey: ["auth", "me"], queryFn: getMe });
      router.replace("/members");
    },
    onError: (error: ApiError) => {
      toast.error(error.detail || "Credenciales inválidas", { duration: 12000 });
    },
  });

  return (
    <Form {...form}>
      {sessionExpired && (
        <div
          role="alert"
          className="mb-5 rounded-lg border border-warning/40 bg-warning/10 px-4 py-3 text-sm text-foreground"
        >
          Tu sesión expiró. Volvé a ingresar.
        </div>
      )}
      <form
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
        className="space-y-5"
      >
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem className="space-y-1.5">
              <FormLabel>
                Email <span className="text-primary">*</span>
              </FormLabel>
              <FormControl>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-2" />
                  <Input
                    type="email"
                    placeholder="owner@gym.com"
                    className="pl-10"
                    {...field}
                  />
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem className="space-y-1.5">
              <FormLabel>
                Contraseña <span className="text-primary">*</span>
              </FormLabel>
              <FormControl>
                <Input type="password" placeholder="••••••••" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <div className="flex items-center justify-between gap-4 pt-2">
          <p className="text-xs text-muted-2">
            ¿Primera vez?{" "}
            <Link href="/register" className="text-primary hover:text-primary/80">
              Crear cuenta
            </Link>
          </p>
          <Button type="submit" size="lg" disabled={mutation.isPending}>
            {mutation.isPending ? "Ingresando..." : "Ingresar"}
            {!mutation.isPending && <ArrowRight className="h-4 w-4" strokeWidth={2.4} />}
          </Button>
        </div>
      </form>
    </Form>
  );
}
