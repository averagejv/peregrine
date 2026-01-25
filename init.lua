-- main nvim conf
print("welcome back <3")

local vim = vim

vim.opt.updatetime = 250

vim.g.mapleader = " "
vim.g.have_nerd_font = true

vim.opt.linebreak = true
vim.opt.winborder = "rounded"
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true
vim.opt.mouse = "a"
vim.opt.undofile = true
vim.opt.ignorecase = true
vim.opt.smartcase = true
vim.opt.signcolumn = "yes"
vim.opt.list = false
vim.opt.cursorline = true
vim.opt.scrolloff = 10

vim.keymap.set({ "n", "x" }, "y", '"+y')
vim.keymap.set("n", "<leader>\\", ":Alpha<CR>")
vim.keymap.set("n", "<leader>v", ":Ex <CR>")
vim.keymap.set("n", "<Esc>", "<cmd>nohlsearch<CR>")
vim.keymap.set("x", "K", ":move '<-2<CR>gv", { silent = true })
vim.keymap.set("x", "J", ":move '>+1<CR>gv", { silent = true })

vim.api.nvim_create_autocmd("InsertEnter", { command = [[set norelativenumber]] })

vim.api.nvim_create_autocmd("InsertLeave", { command = [[set relativenumber]] })

vim.api.nvim_create_autocmd("CursorHold", {
    callback = function()
        vim.diagnostic.open_float(nil, { focusable = false })
    end,
})

vim.api.nvim_create_user_command("Format", function()
    vim.lsp.buf.format()
end, {})

vim.api.nvim_create_user_command("Path", function()
    local path = vim.fn.expand("%:p")
    vim.fn.setreg("+", path)
    print(path)
end, {})

vim.api.nvim_create_autocmd("TextYankPost", {
    group = vim.api.nvim_create_augroup("kickstart-highlight-yank", { clear = true }),
    callback = function()
        vim.highlight.on_yank()
    end,
})

--lazy
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
    local lazyrepo = "https://github.com/folke/lazy.nvim.git"
    local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
    if vim.v.shell_error ~= 0 then
        error("Error cloning lazy.nvim:\n" .. out)
    end
end

vim.opt.rtp:prepend(lazypath)
require("lazy").setup({
    {
        "neovim/nvim-lspconfig",
        dependencies = {
            "williamboman/mason.nvim",
            "williamboman/mason-lspconfig.nvim",
        },
        config = function()
            require("mason").setup()
            require("mason-lspconfig").setup({
                ensure_installed = { "lua_ls", "pyright" },
                automatic_installation = true,
                handlers = {
                    function(server)
                        vim.lsp.config[server].setup({
                            capabilities = capabilities,
                            on_attach = function(_, bufnr)
                                local map = function(mode, lhs, rhs)
                                    vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, silent = true })
                                end
                                map("n", "K", vim.lsp.buf.hover)
                                map("n", "gd", vim.lsp.buf.definition)
                            end,
                        })
                        vim.lsp.config[server].launch()
                    end,
                },
            })
        end,
    },

    {
        "mason-org/mason.nvim",
        opts = {},
    },

    {
        "hrsh7th/nvim-cmp",
        dependencies = { "hrsh7th/cmp-nvim-lsp" },
        config = function()
            local cmp = require("cmp")
            local capabilities = require("cmp_nvim_lsp").default_capabilities()
            cmp.setup({
                mapping = {
                    ["<C-n>"] = cmp.mapping.select_next_item(),
                    ["<C-p>"] = cmp.mapping.select_prev_item(),
                    ["<Tab>"] = cmp.mapping(function(fallback)
                        if cmp.visible() then
                            cmp.select_next_item()
                        else
                            fallback()
                        end
                    end, { "i", "s" }),
                    ["<CR>"] = cmp.mapping.confirm({ select = true }),
                },
                sources = {
                    { name = "nvim_lsp" },
                },
                experimental = {
                    ghost_text = true,
                },
            })
        end,
    },

    {
        "nvim-telescope/telescope.nvim",
        tag = "0.1.8",
        dependencies = { "nvim-lua/plenary.nvim" },
    },

    {
        "goolord/alpha-nvim",
        dependencies = { "nvim-tree/nvim-web-devicons" },
        lazy = true,
        event = "VimEnter",
        config = function()
            if vim.fn.argc() == 0 then
                local alpha = require("alpha")
                local dashboard = require("alpha.themes.dashboard")
                dashboard.section.buttons.val = {
                    dashboard.button("t", "  > tree", ":Ex <CR>"),
                    dashboard.button("f", "  > append", ":Telescope find_files <CR>"),
                    dashboard.button("r", "  > grep", ":Telescope oldfiles <CR>"),
                    dashboard.button("q", "  > bye", ":qa<CR>"),
                }

                dashboard.section.footer.val = {
                    "i put the pro in programmer",
                }
                alpha.setup(dashboard.config)
            end
        end,
    },

    {
        "rebelot/kanagawa.nvim",
        lazy = false,
        priority = 1000,
        config = function()
            vim.cmd("colorscheme kanagawa-dragon")
        end,
    },

    {
        "nvim-mini/mini.nvim",
        version = "*",
        config = function()
            require("mini.ai").setup({ n_lines = 500 })
            require("mini.surround").setup()
            local statusline = require("mini.statusline")
            statusline.setup({ use_icons = vim.g.have_nerd_font })
            statusline.section_location = function()
                return "%2l:%-2v"
            end
        end,
    },

    {
        "nvim-treesitter/nvim-treesitter",
        branch = "master",
        lazy = false,
        build = ":TSUpdate",
        config = function()
            require("nvim-treesitter.configs").setup({
                highlight = {
                    enable = true,
                    additional_vim_regex_highlighting = false,
                },
            })
        end,
    },

    {
        "vyfor/cord.nvim",
        build = ":Cord update",
    },

    {
        "sphamba/smear-cursor.nvim",
        opts = {},
    },

    {
        "nvim-lualine/lualine.nvim",
        dependencies = { "nvim-tree/nvim-web-devicons" },
        opts = {
            component_separators = { left = "", right = "" },
            section_separators = { left = "", right = "" },

            sections = {
                lualine_c = {
                    { "filename", path = 1 },
                },
            },
        },
    },

    {
        'MeanderingProgrammer/render-markdown.nvim',
        dependencies = { 'nvim-treesitter/nvim-treesitter', 'nvim-mini/mini.nvim' }, -- if you use the mini.nvim suite
        ---@module 'render-markdown'
        ---@type render.md.UserConfig
    },
})

vim.o.completeopt = "menu,menuone,noselect"
vim.opt.complete = ""

vim.api.nvim_set_hl(0, "Pmenu", { link = "NormalFloat" })
vim.api.nvim_set_hl(0, "PmenuSel", { link = "Visual" })
vim.api.nvim_set_hl(0, "PmenuBorder", { link = "FloatBorder" })
vim.api.nvim_set_hl(0, "PmenuThumb", { link = "NormalFloat" })
