// Copyright MixUpProject. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PlayerSurvivalComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FHealthChangedSignature, float, CurrentHealth, float, MaxHealth, float, HealthRatio);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FStaminaChangedSignature, float, CurrentStamina, float, MaxStamina, float, StaminaRatio);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FHungerChangedSignature, float, CurrentHunger, float, MaxHunger, float, HungerRatio);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FPlayerSurvivalStatsChangedSignature);

UCLASS(ClassGroup = (Player), meta = (BlueprintSpawnableComponent))
class AI_RE_API UPlayerSurvivalComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UPlayerSurvivalComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(BlueprintAssignable, Category = "Survival|Events")
	FHealthChangedSignature OnHealthChanged;

	UPROPERTY(BlueprintAssignable, Category = "Survival|Events")
	FStaminaChangedSignature OnStaminaChanged;

	UPROPERTY(BlueprintAssignable, Category = "Survival|Events")
	FHungerChangedSignature OnHungerChanged;

	UPROPERTY(BlueprintAssignable, Category = "Survival|Events")
	FPlayerSurvivalStatsChangedSignature OnSurvivalStatsChanged;

	UFUNCTION(BlueprintCallable, Category = "Survival|Health")
	bool ApplyHealthDamage(float DamageAmount);

	UFUNCTION(BlueprintCallable, Category = "Survival|Health")
	bool RestoreHealth(float RestoreAmount);

	UFUNCTION(BlueprintCallable, Category = "Survival|Stamina")
	bool TryConsumeStamina(float Cost);

	UFUNCTION(BlueprintCallable, Category = "Survival|Stamina")
	bool HasEnoughStamina(float Cost) const;

	UFUNCTION(BlueprintPure, Category = "Survival|Health")
	float GetHealthRatio() const { return MaxHP > 0.f ? CurrentHP / MaxHP : 0.f; }

protected:
	UPROPERTY(EditDefaultsOnly, Category = "Survival|Health", meta = (ClampMin = "0.0"))
	float MaxHP = 100.f;
	float CurrentHP = 100.f;

	UPROPERTY(EditDefaultsOnly, Category = "Survival|Stamina", meta = (ClampMin = "0.0"))
	float MaxSP = 100.f;
	float CurrentSP = 100.f;

	UPROPERTY(EditDefaultsOnly, Category = "Survival|Stamina", meta = (ClampMin = "0.0"))
	float StaminaRegenPerSecond = 18.f;

	UPROPERTY(EditDefaultsOnly, Category = "Survival|Hunger", meta = (ClampMin = "0.0"))
	float MaxHunger = 100.f;
	float CurrentHunger = 100.f;

	UPROPERTY(EditDefaultsOnly, Category = "Survival|Hunger", meta = (ClampMin = "0.0"))
	float HungerDrainPerSecond = 0.03f;

	void SetCurrentHealth(float NewHealth);
	void SetCurrentStamina(float NewStamina);
	void SetCurrentHunger(float NewHunger);

	void BroadcastSurvivalStatsChanged();
	
	// ------------------------------ 아래에 변경 추가 ------------------------------
private:
protected:
	
public: 
	FORCEINLINE float GetCurrentSP() const { return CurrentSP; }
	FORCEINLINE float GetCurrentHP() const { return CurrentHP; }
};
