-- Trigger function to automatically update the last_check timestamp
-- whenever a health row is inserted or updated.

create or replace function public.api_health_update_last_check()
returns trigger as $$
begin
  new.last_check = current_timestamp;
  return new;
end;
$$ language plpgsql;

create trigger api_health_update_last_check_trigger
before insert or update on public.api_health
for each row
execute function public.api_health_update_last_check();
