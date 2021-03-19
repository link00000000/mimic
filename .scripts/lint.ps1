$scripts = "lint-imports","lint-code","lint-type_checking","lint-docstring"

$env:PIPENV_VERBOSITY=-1

foreach ($script in $scripts)
{
    $command = "pipenv run " + $script

    Write-Output "Executing: $command"
    Invoke-Expression -Command $command
    Write-Output "done.`r`n"
}

Remove-Item Env:\PIPENV_VERBOSITY
