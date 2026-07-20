#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MixUpDataTypes.h"
#include "SkillComponent.generated.h"

UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class AI_RE_API USkillComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	USkillComponent();

protected:
	virtual void BeginPlay() override;

public:	
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // 3가지 스킬 슬롯 (UI 표시 및 런타임 쿨타임 관리용)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CombatSkills")
	FMixUpSkillData LightSkill;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CombatSkills")
	FMixUpSkillData MediumSkill;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CombatSkills")
	FMixUpSkillData HeavySkill;

    // 스킬 사용 시 쿨타임 갱신 함수
	UFUNCTION(BlueprintCallable, Category = "CombatSkills")
	void MarkSkillAsUsed(int32 SkillSlot);
};
