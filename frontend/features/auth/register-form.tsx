"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Check, Mail, Phone } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getMe } from "@/lib/api/auth";
import { onboardGym } from "@/lib/api/gyms";
import type { ApiError } from "@/lib/types/api";
import { cn } from "@/lib/utils";

const COUNTRIES = [
  "Argentina",
  "Uruguay",
  "Chile",
  "México",
  "España",
  "Otro",
] as const;

const registerSchema = z
  .object({
    gymName: z.string().min(2, "Mínimo 2 caracteres").max(255, "Máximo 255 caracteres"),
    city: z.string().min(2, "Ingresá la ciudad").max(200, "Máximo 200 caracteres"),
    country: z.string().min(1, "Seleccioná un país"),
    gymPhone: z
      .string()
      .min(6, "Mínimo 6 caracteres")
      .max(20, "Máximo 20 caracteres")
      .regex(/^[\d\s+\-()]+$/, "Formato de teléfono inválido"),
    firstName: z.string().min(2, "Mínimo 2 caracteres").max(120, "Máximo 120 caracteres"),
    lastName: z.string().min(2, "Mínimo 2 caracteres").max(120, "Máximo 120 caracteres"),
    email: z.email("Email inválido"),
    password: z.string().min(8, "Mínimo 8 caracteres").max(128, "Máximo 128 caracteres"),
    confirmPassword: z.string().min(8, "Mínimo 8 caracteres"),
    acceptTerms: z.boolean().refine((v) => v === true, { message: "Debés aceptar los términos" }),
    acceptBiometric: z
      .boolean()
      .refine((v) => v === true, { message: "Debés aceptar el consentimiento biométrico" }),
    newsletter: z.boolean().optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Las contraseñas no coinciden",
    path: ["confirmPassword"],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

function getPasswordStrength(password: string): {
  score: number;
  label: string;
  barClass: string;
} {
  if (!password) return { score: 0, label: "", barClass: "" };

  let score = 0;
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;

  if (score <= 2) return { score, label: "Débil", barClass: "weak" };
  if (score <= 3) return { score, label: "Media", barClass: "mid" };
  return { score, label: "Fuerte", barClass: "" };
}

function TermCheckbox({
  checked,
  onChange,
  children,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      className="term-row w-full text-left"
      onClick={() => onChange(!checked)}
    >
      <div className={cn("term-box", checked && "checked")}>
        <Check className="h-3 w-3" strokeWidth={3} />
      </div>
      <div className="text-[13px] leading-relaxed text-muted-foreground">{children}</div>
    </button>
  );
}

export function RegisterForm() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      gymName: "",
      city: "",
      country: "Argentina",
      gymPhone: "",
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptTerms: false,
      acceptBiometric: false,
      newsletter: false,
    },
  });

  const password = form.watch("password");
  const confirmPassword = form.watch("confirmPassword");
  const gymFieldsValid =
    form.watch("gymName").length >= 2 &&
    form.watch("city").length >= 2 &&
    form.watch("gymPhone").length >= 6;

  const strength = useMemo(() => getPasswordStrength(password), [password]);
  const passwordsMatch =
    password.length > 0 && confirmPassword.length > 0 && password === confirmPassword;

  const mutation = useMutation({
    mutationFn: (values: RegisterFormValues) =>
      onboardGym({
        gym_name: values.gymName.trim(),
        gym_address: `${values.city.trim()}, ${values.country}`,
        gym_phone: values.gymPhone.trim(),
        owner_name: `${values.firstName.trim()} ${values.lastName.trim()}`,
        email: values.email.trim().toLowerCase(),
        password: values.password,
      }),
    onSuccess: async () => {
      await queryClient.fetchQuery({ queryKey: ["auth", "me"], queryFn: getMe });
      router.replace("/members");
    },
    onError: (error: ApiError) => {
      const detail = error.detail?.toLowerCase() ?? "";
      if (error.status === 409 || detail.includes("crear")) {
        toast.error("No se pudo crear la cuenta. El email puede estar en uso.", {
          duration: 12000,
        });
        return;
      }
      if (detail.includes("phone") || detail.includes("teléfono")) {
        toast.error(
          "El teléfono del gimnasio no es válido. Usá formato internacional, ej. +54 11 5555 0000",
          { duration: 12000 },
        );
        return;
      }
      toast.error(error.detail || "No se pudo crear la cuenta", { duration: 12000 });
    },
  });

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
        className="form-card mt-0"
      >
        <div className="register-stepper">
          <div className={cn("register-step", gymFieldsValid ? "done" : "active")}>
            <div className="register-step-num">
              {gymFieldsValid ? <Check className="h-3.5 w-3.5" strokeWidth={3} /> : "1"}
            </div>
            <div>
              <p className="text-[13px] font-medium text-foreground">Tu gimnasio</p>
              <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-2">
                Paso 01 · {gymFieldsValid ? "listo" : "en curso"}
              </p>
            </div>
          </div>
          <div className="register-step-divider" />
          <div className="register-step active">
            <div className="register-step-num">2</div>
            <div>
              <p className="text-[13px] font-medium text-foreground">Tu cuenta</p>
              <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-primary">
                Paso 02 · en curso
              </p>
            </div>
          </div>
        </div>

        <div className="form-section">
          <div className="mb-5">
            <div className="section-tag">Paso 01 · Gimnasio</div>
            <h2 className="mt-2.5 text-[19px] font-semibold tracking-[-0.015em]">
              Datos del gimnasio
            </h2>
            <p className="mt-1.5 max-w-[520px] text-[13px] leading-relaxed text-muted-foreground">
              Esta información se muestra en la barra lateral del panel y se usa para generar el
              encabezado de los reportes.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="gymName"
              render={({ field }) => (
                <FormItem className="space-y-1.5">
                  <FormLabel className="field-label">
                    Nombre del gimnasio <span className="text-primary">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input placeholder="ForceFit Club" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="city"
              render={({ field }) => (
                <FormItem className="space-y-1.5">
                  <FormLabel className="field-label">
                    Ciudad <span className="text-primary">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input placeholder="Buenos Aires" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="country"
              render={({ field }) => (
                <FormItem className="space-y-1.5">
                  <FormLabel className="field-label">
                    País <span className="text-primary">*</span>
                  </FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccioná un país" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {COUNTRIES.map((country) => (
                        <SelectItem key={country} value={country}>
                          {country}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="gymPhone"
              render={({ field }) => (
                <FormItem className="space-y-1.5">
                  <FormLabel className="field-label">
                    Tel. del gimnasio <span className="text-primary">*</span>
                  </FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Phone className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-2" />
                      <Input
                        type="tel"
                        placeholder="+54 11 5555 0000"
                        className="pl-10"
                        {...field}
                      />
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </div>

        <div className="form-section">
          <div className="mb-5">
            <div className="section-tag">Paso 02 · Cuenta</div>
            <h2 className="mt-2.5 text-[19px] font-semibold tracking-[-0.015em]">
              Tu cuenta de dueño del gimnasio
            </h2>
            <p className="mt-1.5 max-w-[520px] text-[13px] leading-relaxed text-muted-foreground">
              Vas a ser el administrador principal. Después vas a poder invitar al equipo desde
              Configuración → Usuarios.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="firstName"
              render={({ field }) => (
                <FormItem className="space-y-1.5">
                  <FormLabel className="field-label">
                    Nombre <span className="text-primary">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input placeholder="Mariano" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="lastName"
              render={({ field }) => (
                <FormItem className="space-y-1.5">
                  <FormLabel className="field-label">
                    Apellido <span className="text-primary">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input placeholder="Ortiz" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="mt-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem className="space-y-1.5">
                  <FormLabel className="field-label">
                    Email (será tu usuario) <span className="text-primary">*</span>
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
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem className="space-y-1.5">
                  <FormLabel className="field-label">
                    Contraseña <span className="text-primary">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="••••••••" {...field} />
                  </FormControl>
                  {password.length > 0 && (
                    <>
                      <div className="mt-2 flex gap-1">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <div
                            key={i}
                            className={cn(
                              "pw-bar",
                              i < strength.score && "on",
                              i < strength.score && strength.barClass,
                            )}
                          />
                        ))}
                      </div>
                      <div className="mt-1.5 flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.08em] text-muted-2">
                        <span>Seguridad</span>
                        <span className="text-success">{strength.label}</span>
                      </div>
                    </>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="confirmPassword"
              render={({ field }) => (
                <FormItem className="space-y-1.5">
                  <FormLabel className="field-label">
                    Confirmar contraseña <span className="text-primary">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="••••••••" {...field} />
                  </FormControl>
                  {confirmPassword.length > 0 && (
                    <p
                      className={cn(
                        "text-[11.5px]",
                        passwordsMatch ? "text-success" : "text-destructive",
                      )}
                    >
                      {passwordsMatch ? "Coincide" : "No coincide"}
                    </p>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </div>

        <div className="form-section">
          <div className="mb-5">
            <div className="section-tag">Paso 03 · Términos</div>
            <h2 className="mt-2.5 text-[19px] font-semibold tracking-[-0.015em]">
              Consentimientos
            </h2>
            <p className="mt-1.5 max-w-[520px] text-[13px] leading-relaxed text-muted-foreground">
              Necesitamos tu OK explícito en dos puntos. Los podés revocar cuando quieras desde
              Configuración.
            </p>
          </div>

          <div className="space-y-3">
            <FormField
              control={form.control}
              name="acceptTerms"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <TermCheckbox checked={!!field.value} onChange={field.onChange}>
                      Acepto los{" "}
                      <span className="text-primary">Términos de servicio</span> y la{" "}
                      <span className="text-primary">Política de privacidad</span> de Verifica.
                      Entiendo que el plan arranca con 14 días gratis y que, si no lo cancelo, pasa
                      a US$ 79/mes por sede.
                    </TermCheckbox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="acceptBiometric"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <TermCheckbox checked={!!field.value} onChange={field.onChange}>
                      <strong className="text-foreground">Consentimiento biométrico.</strong>{" "}
                      Entiendo que Verifica va a almacenar datos faciales cifrados de los rostros de
                      mis miembros, y que cada uno deberá firmar su propio consentimiento antes de
                      registrarse.
                    </TermCheckbox>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="newsletter"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <TermCheckbox checked={!!field.value} onChange={field.onChange}>
                      Quiero recibir novedades del producto y un email mensual con el resumen de
                      accesos de mi gimnasio. (Opcional.)
                    </TermCheckbox>
                  </FormControl>
                </FormItem>
              )}
            />
          </div>

          <div className="mt-8 flex flex-col gap-4 border-t border-border pt-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-[13px] text-muted-foreground">
              ¿Ya tenés cuenta?{" "}
              <Link href="/login" className="text-primary hover:text-primary/80">
                Ingresá
              </Link>
            </p>
            <Button type="submit" size="lg" disabled={mutation.isPending}>
              {mutation.isPending ? "Creando cuenta..." : "Crear cuenta"}
              {!mutation.isPending && <ArrowRight className="h-4 w-4" strokeWidth={2.4} />}
            </Button>
          </div>
        </div>
      </form>
    </Form>
  );
}
