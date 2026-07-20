// Copyright MixUpProject. All Rights Reserved.

#include "PlayerSurvivalComponent.h"
#include "Engine/World.h"

UPlayerSurvivalComponent::UPlayerSurvivalComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UPlayerSurvivalComponent::BeginPlay()
{
	Super::BeginPlay();
	
	SetCurrentHealth(MaxHP);
	SetCurrentStamina(MaxSP);
	SetCurrentHunger(MaxHunger);
}

void UPlayerSurvivalComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (CurrentSP < MaxSP)
	{
		SetCurrentStamina(CurrentSP + StaminaRegenPerSecond * DeltaTime);
	}

	if (CurrentHunger > 0.f)
	{
		SetCurrentHunger(CurrentHunger - HungerDrainPerSecond * DeltaTime);
	}
}

bool UPlayerSurvivalComponent::ApplyHealthDamage(float DamageAmount)
{
	if (DamageAmount <= 0.f) return false;
	
	SetCurrentHealth(CurrentHP - DamageAmount);
	return true;
}

bool UPlayerSurvivalComponent::RestoreHealth(float RestoreAmount)
{
	if (RestoreAmount <= 0.f) return false;

	SetCurrentHealth(CurrentHP + RestoreAmount);
	return true;
}

bool UPlayerSurvivalComponent::TryConsumeStamina(float Cost)
{
	if (!HasEnoughStamina(Cost)) return false;

	SetCurrentStamina(CurrentSP - Cost);
	return true;
}

bool UPlayerSurvivalComponent::HasEnoughStamina(float Cost) const
{
	return CurrentSP >= Cost;
}

void UPlayerSurvivalComponent::SetCurrentHealth(float NewHealth)
{
	float Clamped = FMath::Clamp(NewHealth, 0.f, MaxHP);
	if (CurrentHP != Clamped)
	{
		CurrentHP = Clamped;
		OnHealthChanged.Broadcast(CurrentHP, MaxHP, GetHealthRatio());
		BroadcastSurvivalStatsChanged();
	}
}

void UPlayerSurvivalComponent::SetCurrentStamina(float NewStamina)
{
	float Clamped = FMath::Clamp(NewStamina, 0.f, MaxSP);
	if (CurrentSP != Clamped)
	{
		CurrentSP = Clamped;
		OnStaminaChanged.Broadcast(CurrentSP, MaxSP, MaxSP > 0.f ? CurrentSP / MaxSP : 0.f);
		BroadcastSurvivalStatsChanged();
	}
}

void UPlayerSurvivalComponent::SetCurrentHunger(float NewHunger)
{
	float Clamped = FMath::Clamp(NewHunger, 0.f, MaxHunger);
	if (CurrentHunger != Clamped)
	{
		CurrentHunger = Clamped;
		OnHungerChanged.Broadcast(CurrentHunger, MaxHunger, MaxHunger > 0.f ? CurrentHunger / MaxHunger : 0.f);
		BroadcastSurvivalStatsChanged();
	}
}

void UPlayerSurvivalComponent::BroadcastSurvivalStatsChanged()
{
	OnSurvivalStatsChanged.Broadcast();
}
