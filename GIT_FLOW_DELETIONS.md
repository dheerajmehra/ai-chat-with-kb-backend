# Git Flow: Handling File Deletions and Moves

## Current Situation

You're on the `develop` branch with:
- **Deleted files**: Documentation files that were moved/deleted
- **New directory**: `imp_guides_md/` (likely where files were moved)

## Commands to Remove Deletions from Git

### Step 1: Stage All Deletions

```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend

# Stage all deletions (this tells git to remove them from tracking)
git add -u
# OR specifically:
git add -A
```

**What this does:**
- `git add -u` stages all modifications and deletions (but not new files)
- `git add -A` stages everything (additions, modifications, deletions)

### Step 2: Add New Directory (if files were moved there)

```bash
# If you moved files to imp_guides_md/, add that directory
git add imp_guides_md/

# Or if you want to see what's in there first
ls -la imp_guides_md/
```

### Step 3: Verify What Will Be Committed

```bash
# Check what's staged
git status

# See the diff (what will be removed)
git diff --cached --stat
```

### Step 4: Commit Using Git Flow Conventions

```bash
# Commit with a descriptive message
git commit -m "refactor: reorganize documentation into imp_guides_md directory

- Move documentation files to imp_guides_md/
- Remove duplicate/outdated documentation
- Clean up root directory structure"
```

**Commit message format:**
- `refactor:` for reorganizing files
- `chore:` for cleanup tasks
- `docs:` for documentation changes

### Step 5: Push to Develop Branch

```bash
# Push to develop branch
git push origin develop
```

## Complete Command Sequence

```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend

# 1. Stage all deletions and changes
git add -A

# 2. Verify what's staged
git status

# 3. Commit
git commit -m "refactor: reorganize documentation structure"

# 4. Push to develop
git push origin develop
```

## If Files Were Moved (Not Just Deleted)

If you moved files to `imp_guides_md/`, Git can track the move:

```bash
# Stage deletions
git add -u

# Stage new directory
git add imp_guides_md/

# Git will detect the move if content is similar
git status  # Will show "renamed" if detected

# Commit
git commit -m "refactor: move documentation to imp_guides_md directory"
```

## Handling Specific Cases

### Case 1: Files Were Deleted (Not Moved)

```bash
# Remove from git tracking
git rm <file1> <file2> <file3>
# OR stage all deletions
git add -u

# Commit
git commit -m "chore: remove outdated documentation files"
```

### Case 2: Files Were Moved to New Location

```bash
# Git can detect moves automatically
git add -A

# Or explicitly tell git about the move
git mv <old-path> <new-path>

# Commit
git commit -m "refactor: reorganize documentation structure"
```

### Case 3: Some Files Deleted, Some Moved

```bash
# Stage everything
git add -A

# Git will show:
# - deleted: old files
# - new file: new location
# - (possibly "renamed" if content is similar)

# Commit
git commit -m "refactor: reorganize and clean up documentation"
```

## Verification After Commit

```bash
# Check that deletions are committed
git log -1 --stat

# Verify files are removed from git
git ls-files | grep <deleted-file-name>
# Should return nothing if successfully removed
```

## Git Flow Workflow Summary

Since you're on `develop` branch:

1. ✅ **Stage changes**: `git add -A`
2. ✅ **Commit**: `git commit -m "message"`
3. ✅ **Push**: `git push origin develop`
4. ✅ **Later**: When ready, create release branch

## Best Practices

1. **Review before committing:**
   ```bash
   git status
   git diff --cached
   ```

2. **Use descriptive commit messages:**
   - `refactor:` for reorganizing
   - `chore:` for cleanup
   - `docs:` for documentation changes

3. **Verify after commit:**
   ```bash
   git log -1
   git show --stat
   ```

4. **Don't force push to develop** (unless absolutely necessary)

## Troubleshooting

### "Changes not staged for commit"
- Run `git add -A` to stage everything

### "Untracked files" warning
- These are new files. Add them with `git add <file>` if needed

### Want to undo a deletion
```bash
# Restore a deleted file
git restore <file-path>

# Or from a previous commit
git checkout HEAD~1 -- <file-path>
```

### Accidentally committed wrong files
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Or completely remove commit
git reset --hard HEAD~1  # ⚠️ Careful: loses changes
```
